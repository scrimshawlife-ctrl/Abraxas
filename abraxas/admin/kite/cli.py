from __future__ import annotations

import json
import os
from pathlib import Path

from .storage import (
    canonicalize_text,
    export_items,
    insert_item,
    list_items,
    normalize_tags,
    sha256_hex,
    store_file,
)


def register(subparsers) -> None:
    parser = subparsers.add_parser("kite")
    sub = parser.add_subparsers(dest="kite_cmd", required=True)

    init_cmd = sub.add_parser("init")
    init_cmd.set_defaults(func=run_init)

    ingest_cmd = sub.add_parser("ingest")
    ingest_sub = ingest_cmd.add_subparsers(dest="ingest_cmd", required=True)

    ingest_text = ingest_sub.add_parser("text")
    ingest_text.add_argument("--title", required=True)
    ingest_text.add_argument("--tags", default="")
    ingest_text.add_argument("--text", required=True)
    ingest_text.set_defaults(func=run_ingest_text)

    ingest_file = ingest_sub.add_parser("file")
    ingest_file.add_argument("--path", required=True)
    ingest_file.add_argument("--tags", default="")
    ingest_file.set_defaults(func=run_ingest_file)

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.set_defaults(func=run_list)

    export_cmd = sub.add_parser("export")
    export_cmd.add_argument("--out", default=str(Path(".aal/kite/exports/latest")))
    export_cmd.set_defaults(func=run_export)

    serve_cmd = sub.add_parser("serve")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8844)
    serve_cmd.set_defaults(func=run_serve)


def run_init(_args) -> None:
    Path(".aal/kite").mkdir(parents=True, exist_ok=True)
    print(json.dumps({"status": "ok", "root": str(Path('.aal/kite').resolve())}, indent=2))


def run_ingest_text(args) -> None:
    tags = normalize_tags(args.tags.split(","))
    canonical = canonicalize_text(args.text)
    content_sha = sha256_hex(canonical)
    item_id = insert_item(
        title=args.title,
        source_type="text",
        tags=tags,
        content_sha=content_sha,
        file_path=None,
        text_content=canonical,
    )
    print(json.dumps({"item_id": item_id, "content_sha": content_sha}, indent=2))


def run_ingest_file(args) -> None:
    path = Path(args.path)
    data = path.read_bytes()
    content_sha = sha256_hex(data)
    tags = normalize_tags(args.tags.split(","))
    file_path = store_file(path, content_sha)
    item_id = insert_item(
        title=path.stem,
        source_type="file",
        tags=tags,
        content_sha=content_sha,
        file_path=file_path,
        text_content=None,
    )
    print(json.dumps({"item_id": item_id, "content_sha": content_sha, "file_path": file_path}, indent=2))


def run_list(args) -> None:
    rows = list_items(limit=args.limit)
    print(json.dumps({"items": rows}, indent=2))


def run_export(args) -> None:
    out_dir = Path(args.out)
    export_path = export_items(out_dir)
    print(json.dumps({"status": "ok", "export_path": str(export_path)}, indent=2))


def run_serve(args) -> None:
    from importlib.util import find_spec

    if find_spec("fastapi") is None or find_spec("uvicorn") is None:
        raise RuntimeError("fastapi and uvicorn are required for `abx kite serve`")
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()

    @app.get("/kite/items")
    def _items(limit: int = 20):
        return {"items": list_items(limit=limit)}

    uvicorn.run(app, host=args.host, port=args.port)
