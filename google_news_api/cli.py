"""Command-line interface for google-news-api."""

import argparse
import csv
import io
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, TextIO

from . import __version__
from .client import GoogleNewsClient
from .enrichment import ArticleEnricher
from .exceptions import ConfigurationError, GoogleNewsError
from .providers import VALID_SEARCH_MODES
from .results import deduplicate_articles, normalize_articles, sort_articles
from .types import Article

OUTPUT_FIELDS = ("title", "source", "published", "link")
CSV_FIELDS = ("title", "source", "published", "link", "summary", "id", "google_link")


class _DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _add_query_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--exact-phrase", help="Match this exact phrase")
    parser.add_argument(
        "--any-word",
        action="append",
        help="Match at least one of these words (can be used multiple times)",
    )
    parser.add_argument(
        "--exclude-word",
        action="append",
        help="Exclude articles containing this word (can be used multiple times)",
    )
    parser.add_argument("--in-title", help="Ensure this text appears in the title")
    parser.add_argument(
        "--show-query",
        action="store_true",
        help="Print the generated query to stderr before running",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="google-news",
        description="Search Google News RSS feeds from the command line.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search for news articles")
    search.add_argument("query")
    _add_common_options(search)
    search.add_argument("--after")
    search.add_argument("--before")
    search.add_argument("--when")
    _add_domain_options(search)
    _add_query_options(search)

    batch = subparsers.add_parser("batch", help="Search several news queries")
    batch.add_argument("queries", nargs="+")
    _add_common_options(batch)
    batch.add_argument("--after")
    batch.add_argument("--before")
    batch.add_argument("--when")
    _add_domain_options(batch)
    _add_query_options(batch)

    top = subparsers.add_parser("top", help="Fetch top news by topic")
    top.add_argument("--topic", default="WORLD")
    _add_common_options(top)

    location = subparsers.add_parser(
        "location", help="Fetch news for a geographic location"
    )
    location.add_argument(
        "location", help="City, region, or country (e.g. 'New York', 'Bucharest')"
    )
    _add_common_options(location)

    return parser


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--language", default="en")
    parser.add_argument("--country", default="US")
    parser.add_argument("--max-results", type=int)
    parser.add_argument("--mode", choices=VALID_SEARCH_MODES, default="default")
    parser.add_argument(
        "--format",
        choices=("table", "json", "csv"),
        default="table",
        dest="output_format",
    )
    parser.add_argument("--decode-links", action="store_true")
    parser.add_argument("--extract-text", action="store_true")
    parser.add_argument("--deduplicate", action="store_true")
    parser.add_argument("--sort", choices=("newest", "oldest"))
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--force", action="store_true")


def _add_domain_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--include-domain", action="append", dest="include_domains")
    parser.add_argument("--exclude-domain", action="append", dest="exclude_domains")


def _enrich_articles(
    args: argparse.Namespace,
    client: GoogleNewsClient,
    articles: List[Article],
) -> List[Article]:
    if not args.decode_links and not args.extract_text:
        return articles
    try:
        return ArticleEnricher(client, delay=0).enrich(
            articles,
            decode_links=args.decode_links,
            extract_text=args.extract_text,
        )
    except RuntimeError as e:
        raise ConfigurationError(str(e)) from e


def _process_articles(
    args: argparse.Namespace, articles: List[Article]
) -> List[Article]:
    if getattr(args, "deduplicate", False):
        articles = deduplicate_articles(articles)
    if getattr(args, "sort", None):
        articles = sort_articles(articles, newest_first=args.sort == "newest")
    if getattr(args, "normalize", False):
        articles = normalize_articles(articles)  # type: ignore
    return articles


def _write_json(articles: Iterable[Article], output: TextIO) -> None:
    json.dump(list(articles), output, indent=2)
    output.write("\n")


def _write_csv(
    args: argparse.Namespace, articles: Iterable[Article], output: TextIO
) -> None:
    fieldnames = _csv_fields(args)
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for article in articles:
        row = {field: article.get(field) for field in fieldnames}
        if (
            getattr(args, "normalize", False)
            and "published_datetime" in row
            and row["published_datetime"]
        ):
            if isinstance(row["published_datetime"], datetime):
                row["published_datetime"] = row["published_datetime"].isoformat()
        writer.writerow(row)


def _csv_fields(args: argparse.Namespace):
    fieldnames = CSV_FIELDS
    if getattr(args, "extract_text", False):
        fieldnames = (*fieldnames, "text")
    if getattr(args, "normalize", False):
        fieldnames = (*fieldnames, "published_datetime", "source_domain")
    return fieldnames


def _write_table(articles: Iterable[Article], output: TextIO) -> None:
    rows = [
        {field: str(article.get(field) or "") for field in OUTPUT_FIELDS}
        for article in articles
    ]
    widths = {
        field: max([len(field), *(len(row[field]) for row in rows)])
        for field in OUTPUT_FIELDS
    }

    header = "  ".join(field.upper().ljust(widths[field]) for field in OUTPUT_FIELDS)
    separator = "  ".join("-" * widths[field] for field in OUTPUT_FIELDS)
    output.write(f"{header}\n{separator}\n")

    for row in rows:
        output.write(
            "  ".join(row[field].ljust(widths[field]) for field in OUTPUT_FIELDS)
        )
        output.write("\n")


def _write_articles(
    args: argparse.Namespace, articles: List[Article], output: TextIO
) -> None:
    if args.output_format == "json":
        _write_json(articles, output)
    elif args.output_format == "csv":
        _write_csv(args, articles, output)
    else:
        _write_table(articles, output)


def _write_batch_articles(
    args: argparse.Namespace, results: Dict[str, List[Article]], output: TextIO
) -> None:
    if args.output_format == "json":
        json.dump(results, output, indent=2, cls=_DateTimeEncoder)
        output.write("\n")
        return

    if args.output_format == "csv":
        base_fields = _csv_fields(args)
        fieldnames = ("query", *base_fields)
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for query, articles in results.items():
            for article in articles:
                row = {
                    "query": query,
                    **{field: article.get(field) for field in base_fields},
                }
                if (
                    args.normalize
                    and "published_datetime" in row
                    and row["published_datetime"]
                ):
                    row["published_datetime"] = row["published_datetime"].isoformat()
                writer.writerow(row)
        return

    for index, (query, articles) in enumerate(results.items()):
        if index:
            output.write("\n")
        output.write(f"QUERY: {query}\n")
        _write_table(articles, output)


def _run(args: argparse.Namespace, output: TextIO) -> None:
    from google_news_api.query import NewsQuery

    with GoogleNewsClient(language=args.language, country=args.country) as client:
        if args.command == "search":
            query = NewsQuery(
                text=args.query,
                exact_phrase=getattr(args, "exact_phrase", None),
                any_words=getattr(args, "any_word", None),
                exclude_words=getattr(args, "exclude_word", None),
                in_title=getattr(args, "in_title", None),
            ).build()

            if getattr(args, "show_query", False):
                print(query, file=sys.stderr)

            articles = client.search(
                query,
                after=args.after,
                before=args.before,
                when=args.when,
                max_results=args.max_results,
                mode=args.mode,
                include_domains=args.include_domains,
                exclude_domains=args.exclude_domains,
            )
        elif args.command == "batch":
            queries = [
                NewsQuery(
                    text=q,
                    exact_phrase=getattr(args, "exact_phrase", None),
                    any_words=getattr(args, "any_word", None),
                    exclude_words=getattr(args, "exclude_word", None),
                    in_title=getattr(args, "in_title", None),
                ).build()
                for q in args.queries
            ]

            if getattr(args, "show_query", False):
                for q in queries:
                    print(q, file=sys.stderr)

            results = client.batch_search(
                queries,
                after=args.after,
                before=args.before,
                when=args.when,
                max_results=args.max_results,
                mode=args.mode,
                include_domains=args.include_domains,
                exclude_domains=args.exclude_domains,
            )

            processed_results = {}
            for query, articles in results.items():
                articles = _enrich_articles(args, client, articles)
                articles = _process_articles(args, articles)
                processed_results[query] = articles

            _write_batch_articles(args, processed_results, output)
            return
        elif args.command == "location":
            articles = client.location_news(
                location=args.location,
                max_results=args.max_results,
            )
        else:
            articles = client.top_news(
                topic=args.topic,
                max_results=args.max_results,
                mode=args.mode,
            )

        articles = _enrich_articles(args, client, articles)

        articles = _process_articles(args, articles)
        _write_articles(args, articles, output)


def _write_output_file(path: Path, content: str, force: bool) -> None:
    if force:
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=path.parent,
                prefix=f".{path.name}.",
                delete=False,
            ) as output:
                temporary_path = Path(output.name)
                output.write(content)
            os.replace(temporary_path, path)
        except OSError:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
            raise
        return

    created = False
    try:
        with path.open("x", encoding="utf-8", newline="") as output:
            created = True
            output.write(content)
    except OSError:
        if created and path.exists():
            path.unlink()
        raise


def main(
    argv: Optional[Sequence[str]] = None,
    output: TextIO = sys.stdout,
    error: TextIO = sys.stderr,
) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.output is None or args.output == "-":
            _run(args, output)
        else:
            output_path = Path(args.output)
            if output_path.exists() and not args.force:
                print(
                    f"google-news: output file already exists: {output_path}",
                    file=error,
                )
                return 1

            buffered_output = io.StringIO(newline="")
            _run(args, buffered_output)
            _write_output_file(output_path, buffered_output.getvalue(), args.force)
    except GoogleNewsError as e:
        print(f"google-news: {e}", file=error)
        return 1
    except FileExistsError:
        print(f"google-news: output file already exists: {args.output}", file=error)
        return 1
    except OSError as e:
        print(f"google-news: {e}", file=error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
