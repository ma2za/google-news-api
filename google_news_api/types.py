"""Public result types for Google News API clients."""

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
