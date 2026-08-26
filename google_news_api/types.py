"""Public result types for Google News API clients."""

from datetime import datetime
from typing import Optional, TypedDict


class Article(TypedDict):
    title: Optional[str]
    link: Optional[str]
    published: Optional[str]
    summary: str
    source: Optional[str]
    id: Optional[str]


class EnrichedArticle(Article, total=False):
    google_link: str
    text: str


class NormalizedArticle(Article, total=False):
    published_datetime: Optional[datetime]
    source_domain: Optional[str]
