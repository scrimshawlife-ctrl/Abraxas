# Local only by default. Set ABX_PANEL_HOST=0.0.0.0 to expose on LAN.
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("ABX_PANEL_HOST", "127.0.0.1")
    port_raw = os.environ.get("ABX_PANEL_PORT", "8008")
    try:
        port = int(port_raw)
    except ValueError:
        port = 8008
    uvicorn.run("webpanel.app:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
