"""Search providers for Google News compatible results."""

import json
import os
from typing import Any, Dict, List, Optional

import httpx

from .exceptions import ConfigurationError, HTTPError, ParsingError, ValidationError

DEFAULT_MODE = "default"
SEARCHAPI_LIGHT_MODE = "searchapi_light"
SEARCHAPI_PORTAL_MODE = "searchapi_portal"
VALID_SEARCH_MODES = (DEFAULT_MODE, SEARCHAPI_LIGHT_MODE, SEARCHAPI_PORTAL_MODE)


def validate_mode(mode: str) -> None:
    if mode not in VALID_SEARCH_MODES:
        raise ValidationError(
            f"mode must be one of: {', '.join(VALID_SEARCH_MODES)}",
            field="mode",
            value=mode,
        )


class SearchAPIProvider:
    BASE_URL = "https://www.searchapi.io/api/v1/search"
    TIMEOUT = 15.0
    HEADERS = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }

    def search(
        self,
        client: httpx.Client,
        query: str,
        mode: str,
        country: str,
        language: str,
        max_results: Optional[int],
    ) -> List[Dict[str, Any]]:
        params = self._params(query, mode, country, language)
        limit = max_results or 100
        articles = []
        seen_titles = set()

        while len(articles) < limit:
            try:
                response = client.get(
                    self.BASE_URL,
                    params=params,
                    headers=self.HEADERS,
                    timeout=self.TIMEOUT,
                )
                data = self._response_json(response)
            except httpx.RequestError as e:
                raise HTTPError(f"SearchAPI request failed: {str(e)}")

            self._extend_articles(articles, seen_titles, data, limit)
            if self._is_last_page(mode, data):
                break

            params["page"] = params.get("page", 1) + 1

        return self._normalize_articles(articles, max_results)

    async def search_async(
        self,
        client: httpx.AsyncClient,
        query: str,
        mode: str,
        country: str,
        language: str,
        max_results: Optional[int],
    ) -> List[Dict[str, Any]]:
        params = self._params(query, mode, country, language)
        limit = max_results or 100
        articles = []
        seen_titles = set()

        while len(articles) < limit:
            try:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                    headers=self.HEADERS,
                    timeout=self.TIMEOUT,
                )
                data = self._response_json(response)
            except httpx.RequestError as e:
                raise HTTPError(f"SearchAPI request failed: {str(e)}")

            self._extend_articles(articles, seen_titles, data, limit)
            if self._is_last_page(mode, data):
                break

            params["page"] = params.get("page", 1) + 1

        return self._normalize_articles(articles, max_results)

    def _params(
        self, query: str, mode: str, country: str, language: str
    ) -> Dict[str, Any]:
        engine = (
            "google_news_light"
            if mode == SEARCHAPI_LIGHT_MODE
            else "google_news_portal"
        )
        params = {
            "engine": engine,
            "q": query,
            "api_key": self._api_key(),
        }

        if mode == SEARCHAPI_LIGHT_MODE:
            params["gl"] = country.lower()
            params["hl"] = language
        else:
            params["ceid"] = f"{country}:{language}"

        return params

    def _api_key(self) -> str:
        api_key = os.environ.get("SEARCHAPI_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "SearchAPI key not found. Set SEARCHAPI_API_KEY environment variable",
                field="api_key",
                value=None,
            )
        return api_key

    def _response_json(self, response: httpx.Response) -> Dict[str, Any]:
        if not (200 <= response.status_code < 400):
            raise HTTPError(
                f"SearchAPI request failed: {response.status_code}",
                status_code=response.status_code,
                response_text=response.text,
            )

        try:
            return response.json()
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ParsingError(
                "Failed to parse SearchAPI response",
                data=response.text,
                error=e,
            )

    def _extend_articles(
        self,
        articles: List[Dict[str, Any]],
        seen_titles: set[str],
        data: Dict[str, Any],
        limit: int,
    ) -> None:
        for article in data.get("organic_results", []):
            title = article.get("title", "").lower()
            if title not in seen_titles:
                seen_titles.add(title)
                articles.append(article)
                if len(articles) >= limit:
                    break

    def _is_last_page(self, mode: str, data: Dict[str, Any]) -> bool:
        page_results = data.get("organic_results", [])
        return mode != SEARCHAPI_LIGHT_MODE or len(page_results) < 10

    def _normalize_articles(
        self,
        articles: List[Dict[str, Any]],
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if max_results == 0:
            return []

        selected = articles[:max_results] if max_results else articles
        return [
            {
                "title": article.get("title"),
                "link": article.get("link"),
                "published": article.get("published")
                or article.get("date")
                or article.get("iso_date"),
                "summary": article.get("summary") or article.get("snippet", ""),
                "source": self._source_name(article.get("source")),
            }
            for article in selected
        ]

    def _source_name(self, source: Any) -> Any:
        if isinstance(source, dict):
            return source.get("name")
        return source


SEARCHAPI_PROVIDER = SearchAPIProvider()
