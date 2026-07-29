"""Command-line interface for google-news-api."""

import argparse
import csv
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, TextIO

from . import __version__
from .client import GoogleNewsClient
from .exceptions import GoogleNewsError
from .providers import VALID_SEARCH_MODES
from .types import Article, EnrichedArticle

OUTPUT_FIELDS = ("title", "source", "published", "link")
CSV_FIELDS = ("title", "source", "published", "link", "summary", "id", "google_link")


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

    batch = subparsers.add_parser("batch", help="Search several news queries")
    batch.add_argument("queries", nargs="+")
    _add_common_options(batch)
    batch.add_argument("--after")
    batch.add_argument("--before")
    batch.add_argument("--when")
    _add_domain_options(batch)

    top = subparsers.add_parser("top", help="Fetch top news by topic")
    top.add_argument("--topic", default="WORLD")
    _add_common_options(top)

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
    parser.add_argument("--output")
    parser.add_argument("--force", action="store_true")


def _add_domain_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--include-domain", action="append", dest="include_domains")
    parser.add_argument("--exclude-domain", action="append", dest="exclude_domains")


def _decode_articles(
    client: GoogleNewsClient, articles: List[Article]
) -> List[EnrichedArticle]:
    urls = [article["link"] for article in articles if article.get("link")]
    decoded_urls = client.decode_urls(urls, delay=0)
    decoded_by_url = dict(zip(urls, decoded_urls))

    enriched_articles: List[EnrichedArticle] = []
    for article in articles:
        enriched = dict(article)
        link = article.get("link")
        decoded_url = decoded_by_url.get(link) if link else None
        if decoded_url:
            enriched["google_link"] = link
            enriched["link"] = decoded_url
        enriched_articles.append(enriched)

    return enriched_articles


def _write_json(articles: Iterable[Article], output: TextIO) -> None:
    json.dump(list(articles), output, indent=2)
    output.write("\n")


def _write_csv(articles: Iterable[Article], output: TextIO) -> None:
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for article in articles:
        writer.writerow({field: article.get(field) for field in CSV_FIELDS})


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
    articles: List[Article], output_format: str, output: TextIO
) -> None:
    if output_format == "json":
        _write_json(articles, output)
    elif output_format == "csv":
        _write_csv(articles, output)
    else:
        _write_table(articles, output)


def _write_batch_articles(
    results: Dict[str, List[Article]], output_format: str, output: TextIO
) -> None:
    if output_format == "json":
        json.dump(results, output, indent=2)
        output.write("\n")
        return

    if output_format == "csv":
        fieldnames = ("query", *CSV_FIELDS)
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for query, articles in results.items():
            for article in articles:
                writer.writerow(
                    {
                        "query": query,
                        **{field: article.get(field) for field in CSV_FIELDS},
                    }
                )
        return

    for index, (query, articles) in enumerate(results.items()):
        if index:
            output.write("\n")
        output.write(f"QUERY: {query}\n")
        _write_table(articles, output)


def _run(args: argparse.Namespace, output: TextIO) -> None:
    with GoogleNewsClient(language=args.language, country=args.country) as client:
        if args.command == "search":
            articles = client.search(
                args.query,
                after=args.after,
                before=args.before,
                when=args.when,
                max_results=args.max_results,
                mode=args.mode,
                include_domains=args.include_domains,
                exclude_domains=args.exclude_domains,
            )
        elif args.command == "batch":
            results = client.batch_search(
                args.queries,
                after=args.after,
                before=args.before,
                when=args.when,
                max_results=args.max_results,
                mode=args.mode,
                include_domains=args.include_domains,
                exclude_domains=args.exclude_domains,
            )
            if args.decode_links:
                results = {
                    query: _decode_articles(client, articles)
                    for query, articles in results.items()
                }
            _write_batch_articles(results, args.output_format, output)
            return
        else:
            articles = client.top_news(
                topic=args.topic,
                max_results=args.max_results,
                mode=args.mode,
            )

        if args.decode_links:
            articles = _decode_articles(client, articles)

        _write_articles(articles, args.output_format, output)


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
