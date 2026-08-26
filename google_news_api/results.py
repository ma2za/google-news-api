"""Pure helper functions for result normalization and deduplication."""

import email.utils
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Iterable, List, Mapping, Optional

from .exceptions import ValidationError
from .types import Article, NormalizedArticle


def parse_published(value: Optional[str]) -> Optional[datetime]:
    """
    Parse an RFC 2822 published date into a timezone-aware UTC datetime.

    If the date is missing, invalid, or cannot be parsed, returns None.
    Naive parsed dates are treated as UTC.
    """
    if not value:
        return None

    try:
        parsed_dt = email.utils.parsedate_to_datetime(value)
        if parsed_dt.tzinfo is None:
            # Treat naive dates as UTC
            parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
        return parsed_dt
    except (TypeError, ValueError):
        return None


def source_domain(article: Mapping[str, Any]) -> Optional[str]:
    """
    Extract the source domain from an article.

    Prefers a decoded link. If the link is an undecoded Google News URL,
    returns None rather than pretending the publisher name is a domain.
    """
    link = article.get("link")
    if not link:
        return None

    # Check if it's an undecoded Google News link
    if "news.google.com/rss/articles/" in link or "news.google.com/articles/" in link:
        return None

    try:
        parsed = urllib.parse.urlparse(link)
        hostname = parsed.hostname
        if hostname:
            return hostname.lower()
        return None
    except ValueError:
        return None


def deduplicate_articles(
    articles: Iterable[Article],
    *,
    by: str = "id",
) -> List[Article]:
    """
    Deduplicate an iterable of articles predictably, keeping the first occurrence.

    Falls back to 'link', then normalized 'title' if the requested key is missing.
    Articles missing all identity attributes remain distinct.

    Args:
        articles: The articles to deduplicate.
        by: The primary key to deduplicate by ("id", "link", or "title").
            Defaults to "id".

    Raises:
        ValidationError: If 'by' is not one of "id", "link", or "title".
    """
    if by not in ("id", "link", "title"):
        raise ValidationError(f"Invalid deduplication key: {by}", value=by)

    seen = set()
    deduplicated = []

    for article in articles:
        identity = None

        # Try requested key first
        if by == "id" and article.get("id"):
            identity = f"id:{article['id']}"
        elif by == "link" and article.get("link"):
            identity = f"link:{article['link']}"
        elif by == "title" and article.get("title"):
            normalized_title = " ".join(article["title"].lower().split())
            identity = f"title:{normalized_title}"

        # Fallbacks if requested key was missing
        if not identity:
            if by != "id" and article.get("id"):
                identity = f"id:{article['id']}"
            elif by != "link" and article.get("link"):
                identity = f"link:{article['link']}"
            elif by != "title" and article.get("title"):
                normalized_title = " ".join(article["title"].lower().split())
                identity = f"title:{normalized_title}"

        if identity is None:
            # Cannot identify, keep it distinct
            deduplicated.append(article)
            continue

        if identity not in seen:
            seen.add(identity)
            deduplicated.append(article)

    return deduplicated


def sort_articles(
    articles: Iterable[Article],
    *,
    newest_first: bool = True,
) -> List[Article]:
    """
    Stably sort articles chronologically by their published date.

    Undated articles (or articles with invalid dates) are always placed last,
    regardless of sort direction.
    """

    def _sort_key(article: Article) -> Any:
        dt = parse_published(article.get("published"))
        if dt is None:
            # Undated goes last.
            # In descending (newest_first=True), we return a minimal timezone-aware datetime.
            # In ascending (newest_first=False), we return a maximal timezone-aware datetime.
            if newest_first:
                return datetime.min.replace(tzinfo=timezone.utc)
            return datetime.max.replace(tzinfo=timezone.utc)
        return dt

    return sorted(articles, key=_sort_key, reverse=newest_first)


def normalize_article(article: Article) -> NormalizedArticle:
    """
    Return a new NormalizedArticle with published_datetime and source_domain
    added, without mutating the input dictionary.
    """
    normalized = NormalizedArticle(**article)  # type: ignore

    dt = parse_published(article.get("published"))
    if dt is not None:
        normalized["published_datetime"] = dt

    domain = source_domain(article)
    if domain is not None:
        normalized["source_domain"] = domain

    return normalized


def normalize_articles(articles: Iterable[Article]) -> List[NormalizedArticle]:
    """Normalize an iterable of articles without mutation."""
    return [normalize_article(article) for article in articles]
