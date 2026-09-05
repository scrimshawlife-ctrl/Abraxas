"""Notion REST client with timeouts and deterministic retry backoff."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping
from urllib.request import OpenerDirector

from abraxas.research_rag.config import ResearchRagConfig
from abraxas.research_rag.errors import NotionTransportError
from abraxas.research_rag.logging_util import log_fail

Sleeper = Callable[[float], None]
RETRY_STATUSES = frozenset({429, 502, 503, 504})
NOTION_API = "https://api.notion.com/v1"


def backoff_seconds(attempt: int, base: float = 0.25, cap: float = 8.0) -> float:
    """Exponential delay plus deterministic jitter. No PRNG in control logic."""
    exp = min(cap, base * (2**attempt))
    jitter = base * (0.1 * ((attempt * 37) % 10))
    return exp + jitter


class NotionHttpStore:
    """Live Notion data-source query/create/update. Secrets stay in headers only."""

    def __init__(
        self,
        config: ResearchRagConfig,
        *,
        opener: OpenerDirector | None = None,
        urlopen: Callable[..., Any] | None = None,
        sleeper: Sleeper | None = None,
    ) -> None:
        self._config = config
        self._token = config.require_token()
        self._opener = opener
        self._urlopen = urlopen or urllib.request.urlopen
        self._sleeper = sleeper or _default_sleep

    def query_data_source(
        self,
        data_source_id: str,
        *,
        filter: Mapping[str, Any] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            body: dict[str, Any] = {"page_size": page_size}
            if filter:
                body["filter"] = dict(filter)
            if cursor:
                body["start_cursor"] = cursor
            payload = self._request("POST", f"/data_sources/{data_source_id}/query", body)
            pages.extend(list(payload.get("results") or []))
            if not payload.get("has_more"):
                return pages
            cursor = str(payload.get("next_cursor") or "")
            if not cursor:
                return pages

    def create_page(self, data_source_id: str, properties: Mapping[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/pages",
            {
                "parent": {"type": "data_source_id", "data_source_id": data_source_id},
                "properties": dict(properties),
            },
        )

    def update_page(self, page_id: str, properties: Mapping[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/pages/{page_id}", {"properties": dict(properties)})

    def get_page(self, page_id: str) -> dict[str, Any]:
        return self._request("GET", f"/pages/{page_id}", None)

    def _request(self, method: str, path: str, body: Mapping[str, Any] | None) -> dict[str, Any]:
        last_error: Exception | None = None
        attempts = max(1, int(self._config.max_retries) + 1)
        for attempt in range(attempts):
            try:
                return self._once(method, path, body)
            except NotionTransportError as exc:
                last_error = exc
                retryable = exc.status_code in RETRY_STATUSES or exc.status_code is None
                if not retryable or attempt >= attempts - 1:
                    log_fail(
                        "notion_http_exhausted",
                        method=method,
                        path=path,
                        status_code=exc.status_code,
                        attempt=attempt,
                    )
                    raise
                delay = backoff_seconds(attempt)
                log_fail(
                    "notion_http_retry",
                    method=method,
                    path=path,
                    status_code=exc.status_code,
                    attempt=attempt,
                    delay_s=delay,
                )
                self._sleeper(delay)
        raise NotionTransportError(str(last_error), status_code=None)

    def _once(self, method: str, path: str, body: Mapping[str, Any] | None) -> dict[str, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{NOTION_API}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "Notion-Version": self._config.notion_version,
            },
        )
        try:
            if self._opener is not None:
                response = self._opener.open(request, timeout=self._config.timeout_s)
            else:
                response = self._urlopen(request, timeout=self._config.timeout_s)
            with response:
                raw = response.read()
            if not raw:
                return {}
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise NotionTransportError("notion_non_object_response")
            return parsed
        except urllib.error.HTTPError as exc:
            raise NotionTransportError(
                f"notion_http_error:{exc.code}",
                status_code=int(exc.code),
            ) from exc
        except urllib.error.URLError as exc:
            raise NotionTransportError(f"notion_transport_error:{exc.reason}") from exc


def _default_sleep(seconds: float) -> None:
    import time

    time.sleep(seconds)


def connect_from_env(environ: Mapping[str, str] | None = None) -> NotionHttpStore:
    return NotionHttpStore(ResearchRagConfig.from_env(environ))
