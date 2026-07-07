"""Almatjar Althaki store core as a local HTTP service.

``POST /api/handle`` accepts ``{"message": "..."}`` and returns the store
action (ANSWER / CREATE_DRAFT_ORDER / ESCALATE_SUPPORT) with recommendations.
Draft-only by design: no payment and no real order is ever created. The
catalog loads once at startup (``ALMATJAR_CATALOG``, default
``<project>/data/catalog.json``; falls back to the built-in default catalog).
"""

from __future__ import annotations

import os
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .http_base import BaseServiceHandler, build_server
from .store import handle_store_message, load_catalog

_CATALOG: list[dict[str, Any]] | None = None


def catalog_path() -> Path:
    raw = os.environ.get("ALMATJAR_CATALOG", "").strip()
    return Path(raw) if raw else PROJECT_ROOT / "data" / "catalog.json"


def _handle_route(data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    message = str(data.get("message") or "").strip()
    if not message:
        return 400, {"ok": False, "error": "missing 'message'"}
    if _CATALOG is None:
        return 503, {"ok": False, "error": "catalog not loaded"}
    return 200, {"ok": True, **handle_store_message(message, _CATALOG)}


class Handler(BaseServiceHandler):
    post_routes = {"/api/handle": staticmethod(_handle_route)}


def create_server(host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    global _CATALOG
    _CATALOG = load_catalog(catalog_path())
    return build_server(Handler, host=host, port=port)


def run_server(host: str | None = None, port: int | None = None) -> None:
    from .version import __version__

    server = create_server(host=host, port=port)
    print(f"almatjar service v{__version__}: http://{server.server_address[0]}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
