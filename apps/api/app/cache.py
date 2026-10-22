"""HTTP cache headers for read-only aggregate endpoints."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

UNCACHED_PATHS = {"/api/health"}


def resolve_dataset_id(manifest_path: Path, parquet_path: Path) -> str:
    """Prefer the source checksum, then the cutoff, then the file timestamp."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        value = manifest.get("source_sha256") or manifest.get("corte_actual")
        if value:
            return str(value)
    except (OSError, json.JSONDecodeError):
        pass
    try:
        return str(int(parquet_path.stat().st_mtime))
    except OSError:
        return "unknown"


class CacheHeadersMiddleware(BaseHTTPMiddleware):
    """Add ETag + Cache-Control to successful GET requests under /api/."""

    def __init__(self, app, *, dataset: str, max_age: int = 300) -> None:
        super().__init__(app)
        self.dataset = dataset
        self.max_age = max_age

    def _etag(self, request: Request) -> str:
        resource = f"{request.url.path}?{request.url.query}"
        token = hashlib.sha256(f"{self.dataset}|{resource}".encode()).hexdigest()[:16]
        return f'"{token}"'

    async def dispatch(self, request: Request, call_next):
        if (
            request.method != "GET"
            or not request.url.path.startswith("/api/")
            or request.url.path in UNCACHED_PATHS
        ):
            return await call_next(request)

        response = await call_next(request)
        if response.status_code != 200:
            return response

        etag = self._etag(request)
        cache_control = (
            f"public, max-age={self.max_age}, "
            f"stale-while-revalidate={self.max_age * 2}"
        )
        if request.headers.get("if-none-match") in {etag, "*"}:
            return Response(
                status_code=304,
                headers={"ETag": etag, "Cache-Control": cache_control},
            )

        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = cache_control
        return response
