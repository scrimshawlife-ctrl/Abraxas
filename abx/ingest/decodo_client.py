from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, Literal
import base64
import json
import os
import urllib.request
import urllib.error

DecodoMode = Literal["realtime", "tasks"]

@dataclass(frozen=True)
class DecodoConfig:
    auth_b64: str
    endpoint: str
    mode: DecodoMode
    timeout_s: float = 30.0

def load_decodo_config() -> DecodoConfig:
    auth_b64 = os.environ.get("DECODO_AUTH_B64", "").strip()
    if not auth_b64:
        raise RuntimeError("Missing DECODO_AUTH_B64 (base64(user:pass))")
    mode = os.environ.get("DECODO_MODE", "realtime").strip().lower()
    if mode not in ("realtime", "tasks"):
        mode = "realtime"
    endpoint = os.environ.get("DECODO_ENDPOINT", "https://scraper-api.decodo.com/v2/scrape").strip()
    return DecodoConfig(auth_b64=auth_b64, endpoint=endpoint, mode=mode)  # type: ignore

def _post_json(url: str, auth_b64: str, payload: Dict[str, Any], timeout_s: float) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, method="POST", data=data)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("Authorization", f"Basic {auth_b64}")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            body = r.read().decode("utf-8")
            # Decodo returns JSON for realtime; tasks may return JSON with IDs
            try:
                return json.loads(body)
            except Exception:
                return {"raw": body}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        raise RuntimeError(f"Decodo HTTPError {e.code}: {body[:500]}")
    except Exception as e:
        raise RuntimeError(f"Decodo request failed: {e}")

def scrape_url(url: str, *, target: str = "universal", headless: str = "html", locale: str = "en-us", device_type: str = "desktop") -> Dict[str, Any]:
    cfg = load_decodo_config()
    # Realtime API payload shape (aligned with Decodo examples); keep minimal.
    payload = {
        "target": target,
        "url": url,
        "headless": headless,       # "html" for HTML output; may support json/markdown depending on plan
        "locale": locale,
        "device_type": device_type,
    }
    return _post_json(cfg.endpoint, cfg.auth_b64, payload, cfg.timeout_s)
