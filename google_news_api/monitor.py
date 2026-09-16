import json
import os
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Set

from google_news_api.types import Article


class ArticleTracker:
    def __init__(self, state_path: str, *, max_seen: int = 10_000):
        self._state_path = state_path
        self._max_seen = max_seen
        self._version = 1

    def _get_identity(self, article: Dict[str, Any]) -> Optional[str]:
        if article.get("id"):
            return f"id:{article['id']}"

        link = article.get("link")
        google_link = article.get("google_link")

        if link and google_link:
            # Enriched article: link is decoded publisher link, google_link is original
            return f"link:{link}"
        if link:
            # Original link
            return f"link:{link}"
        if google_link:
            return f"link:{google_link}"

        title = article.get("title")
        if title:
            norm_title = " ".join(title.lower().split())
            pub = article.get("published", "")
            return f"title:{norm_title}:{pub}"

        return None

    def filter_new(
        self,
        articles: Iterable[Article],
        *,
        fingerprint: str,
        emit_existing: bool = False,
    ) -> List[Article]:
        is_first_run = not os.path.exists(self._state_path)

        if is_first_run:
            seen_identities: List[str] = []
            seen_set: Set[str] = set()
            saved_fingerprint = fingerprint
        else:
            with open(self._state_path, "r", encoding="utf-8") as f:
                state = json.load(f)

            saved_fingerprint = state.get("fingerprint")
            if saved_fingerprint != fingerprint:
                raise ValueError(
                    f"Fingerprint mismatch: expected {saved_fingerprint}, "
                    f"got {fingerprint}"
                )

            seen_identities = state.get("identities", [])
            seen_set = set(seen_identities)

        new_articles = []

        for article in articles:
            identity = self._get_identity(article)

            if identity is None:
                # Cannot identify, always treat as new
                new_articles.append(article)
                continue

            if identity not in seen_set:
                new_articles.append(article)
                seen_set.add(identity)
                seen_identities.append(identity)

        if len(seen_identities) > self._max_seen:
            seen_identities = seen_identities[-self._max_seen :]

        new_state = {
            "version": self._version,
            "fingerprint": fingerprint,
            "identities": seen_identities,
        }

        dir_name = os.path.dirname(os.path.abspath(self._state_path))
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        try:
            fd, temp_path = tempfile.mkstemp(
                dir=dir_name, prefix=".", suffix=".tmp", text=True
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(new_state, f)
            os.replace(temp_path, self._state_path)
        except Exception:
            if "temp_path" in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise

        if is_first_run and not emit_existing:
            return []

        return new_articles
