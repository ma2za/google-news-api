"""NewsQuery builder for constructing Google News search strings."""

from typing import List, Optional

from google_news_api.exceptions import ValidationError


def _escape(term: str) -> str:
    """Escape embedded quotes and backslashes deterministically."""
    return term.replace('\\', '\\\\').replace('"', '\\"')


def _quote_term(term: str) -> str:
    """Quote a term if it contains spaces and is not already quoted."""
    if " " in term and not (term.startswith('"') and term.endswith('"')):
        return f'"{term}"'
    return term


def _clean_list(items: Optional[List[str]]) -> List[str]:
    """Strip items, remove empty items, and preserve order while removing duplicates."""
    if not items:
        return []

    cleaned = []
    seen = set()
    for item in items:
        if not isinstance(item, str):
            continue
        stripped = item.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            cleaned.append(stripped)
    return cleaned


class NewsQuery:
    """Immutable builder for Google News search queries.

    This helps safely construct advanced search queries using exact phrases,
    any-word matching, exclusions, and title targeting.
    """

    def __init__(
        self,
        text: str = "",
        *,
        exact_phrase: Optional[str] = None,
        any_words: Optional[List[str]] = None,
        exclude_words: Optional[List[str]] = None,
        in_title: Optional[str] = None,
    ):
        self.text = text.strip() if isinstance(text, str) else ""
        self.exact_phrase = (
            exact_phrase.strip() if isinstance(exact_phrase, str) else None
        )
        if self.exact_phrase == "":
            self.exact_phrase = None

        self.any_words = tuple(_clean_list(any_words))
        self.exclude_words = tuple(_clean_list(exclude_words))

        self.in_title = in_title.strip() if isinstance(in_title, str) else None
        if self.in_title == "":
            self.in_title = None

        if not any([self.text, self.exact_phrase, self.any_words, self.in_title]):
            raise ValidationError(
                "At least one positive term (text, exact_phrase, any_words, or "
                "in_title) is required.",
                field="query",
                value="",
            )

    def build(self) -> str:
        """Build the final search query string."""
        parts = []

        if self.text:
            parts.append(self.text)

        if self.exact_phrase:
            escaped = _escape(self.exact_phrase)
            parts.append(f'"{escaped}"')

        if self.any_words:
            escaped_words = [_quote_term(_escape(word)) for word in self.any_words]
            parts.append(f"({' OR '.join(escaped_words)})")

        if self.exclude_words:
            escaped_excludes = [
                _quote_term(_escape(word)) for word in self.exclude_words
            ]
            for word in escaped_excludes:
                parts.append(f"-{word}")

        if self.in_title:
            escaped = _escape(self.in_title)
            parts.append(f'intitle:"{escaped}"')

        return " ".join(parts)

    def __str__(self) -> str:
        return self.build()
