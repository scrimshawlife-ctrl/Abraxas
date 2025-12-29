from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Protocol


@dataclass(frozen=True)
class FetchResult:
    ok: bool
    final_url: str
    redirect_chain: List[str]
    headers: Dict[str, str]
    body: bytes
    offline: bool = False
    reason: str = ""


class FetchAdapter(Protocol):
    def fetch(self, url: str, timeout_s: int = 25) -> FetchResult: ...


class UrllibFetchAdapter:
    """
    Fallback adapter. Redirect chain may be limited depending on stdlib behavior.
    We still return a best-effort chain of [url, final_url] if different.
    """

    def fetch(self, url: str, timeout_s: int = 25) -> FetchResult:
        if not url:
            return FetchResult(
                ok=False,
                final_url="",
                redirect_chain=[],
                headers={},
                body=b"",
                offline=True,
                reason="no_url",
            )
        try:
            import urllib.request

            req = urllib.request.Request(
                url, headers={"User-Agent": "AbraxasMediaOrigin/0.2"}
            )
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                final_url = resp.geturl()
                headers = {k.lower(): v for k, v in dict(resp.headers).items()}
                body = resp.read()
            chain = [url]
            if final_url and final_url != url:
                chain.append(final_url)
            return FetchResult(
                ok=True,
                final_url=final_url or url,
                redirect_chain=chain,
                headers=headers,
                body=body,
            )
        except Exception as e:
            return FetchResult(
                ok=False,
                final_url=url,
                redirect_chain=[url],
                headers={},
                body=b"",
                offline=False,
                reason=repr(e),
            )


class DecodoFetchAdapter:
    """
    Decodo adapter placeholder: integrates via environment variables and/or your existing acquisition layer.
    The goal is to return real redirect chains when Decodo is available.
    """

    def __init__(self) -> None:
        self.endpoint = os.environ.get("DECODO_FETCH_ENDPOINT", "").strip()

    def fetch(self, url: str, timeout_s: int = 25) -> FetchResult:
        if not url:
            return FetchResult(
                ok=False,
                final_url="",
                redirect_chain=[],
                headers={},
                body=b"",
                offline=True,
                reason="no_url",
            )
        if not self.endpoint:
            return FetchResult(
                ok=False,
                final_url=url,
                redirect_chain=[url],
                headers={},
                body=b"",
                offline=True,
                reason="decodo_endpoint_not_configured",
            )
        try:
            import json
            import urllib.request

            payload = json.dumps({"url": url, "timeout_s": timeout_s}).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "AbraxasDecodoAdapter/0.1",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read()
            obj = json.loads(raw.decode("utf-8", errors="ignore"))
            ok = bool(obj.get("ok"))
            final_url = str(obj.get("final_url") or url)
            chain = (
                obj.get("redirect_chain")
                if isinstance(obj.get("redirect_chain"), list)
                else [url, final_url]
            )
            chain = [str(x) for x in chain if str(x).strip()]
            headers = obj.get("headers") if isinstance(obj.get("headers"), dict) else {}
            body = b""
            if isinstance(obj.get("body_b64"), str) and obj.get("body_b64"):
                import base64

                body = base64.b64decode(obj["body_b64"].encode("utf-8"))
            return FetchResult(
                ok=ok,
                final_url=final_url,
                redirect_chain=chain,
                headers={str(k).lower(): str(v) for k, v in headers.items()},
                body=body,
            )
        except Exception as e:
            return FetchResult(
                ok=False,
                final_url=url,
                redirect_chain=[url],
                headers={},
                body=b"",
                offline=False,
                reason=repr(e),
            )


def choose_adapter(provider: str) -> FetchAdapter:
    p = (provider or "").strip().lower()
    if p == "decodo":
        return DecodoFetchAdapter()
    return UrllibFetchAdapter()
