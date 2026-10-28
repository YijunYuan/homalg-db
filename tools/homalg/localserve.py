"""The optional FastAPI transport for static-equivalent local database snapshots."""

import hashlib
import re
from pathlib import Path

from homalg.localdb import Database, compact
from homalg.repository import DOC_KEY


def create_app(static: Path, db: Path | None = None):
    """Serve static files alone or add the documented read-only /api data source."""
    try:
        from fastapi import FastAPI, HTTPException, Query, Request
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse, Response
        from fastapi.staticfiles import StaticFiles
    except ImportError as error:
        raise ValueError("Local serving requires: uv sync --project tools --extra serve") from error

    static = static.resolve()
    if not static.is_dir():
        raise ValueError(f"Static directory does not exist: {static}")
    app = FastAPI(title="HomAlgDB local data source", docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://(?:localhost|127\.0\.0\.1|\[::1\])(?::\d+)?",
        allow_methods=["GET"],
        expose_headers=["X-Homalg-Truncated", "ETag"],
    )

    @app.exception_handler(KeyError)
    async def missing(_request: Request, error: KeyError):
        return JSONResponse({"detail": f"Not found: {error.args[0]}"}, status_code=404)

    @app.exception_handler(ValueError)
    async def invalid(_request: Request, error: ValueError):
        return JSONResponse({"detail": str(error)}, status_code=400)

    if db is not None:
        database = Database(db)
        app.state.database = database

        def doc_key(key: str) -> None:
            if not DOC_KEY.fullmatch(key):
                raise HTTPException(status_code=404, detail="Invalid document key")

        def identifier(key: str, local: str) -> str:
            doc_key(key)
            if not re.fullmatch(r"[A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*", local):
                raise HTTPException(status_code=404, detail="Invalid local id")
            return f"{key}.{local}"

        @app.get("/api/manifest")
        def manifest(request: Request):
            payload = compact(database.resource("manifest.json"))
            etag = '"' + hashlib.sha256(payload.encode()).hexdigest() + '"'
            headers = {"ETag": etag, "Cache-Control": "no-cache"}
            if request.headers.get("if-none-match") == etag:
                return Response(status_code=304, headers=headers)
            return Response(payload, media_type="application/json", headers=headers)

        @app.get("/api/documents/{key}")
        def document(key: str, chapter: str | None = Query(default=None, max_length=200)):
            doc_key(key)
            return database.document(key, chapter)

        @app.get("/api/nodes/{key}/{local}")
        def node(key: str, local: str):
            return database.node(identifier(key, local))

        @app.get("/api/nodes/{key}/{local}/neighbors")
        def neighbors(
            key: str, local: str, dir: str = "up", depth: int = Query(default=1, ge=1, le=3)
        ):
            records, truncated = database.neighbors(identifier(key, local), dir, depth)
            return JSONResponse(records, headers={"X-Homalg-Truncated": str(truncated).lower()})

        @app.get("/api/search")
        def search(request: Request):
            if len(request.query_params) != len(request.query_params.multi_items()):
                raise ValueError("Use comma-separated lists instead of duplicate search parameters")
            return database.search(dict(request.query_params))

        @app.get("/api/taxonomy")
        def taxonomy():
            return database.resource("taxonomy.json")

        @app.get("/api/global-graph")
        def global_graph():
            return database.resource("global-graph.json")

        @app.get("/api/global-dag")
        def global_dag(first: int = Query(alias="from"), last: int = Query(alias="to")):
            return database.global_dag(first, last)

        @app.get("/api/evolution/{concept}")
        def evolution(concept: str):
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", concept):
                raise HTTPException(status_code=404, detail="Invalid concept id")
            return database.resource(f"evolution/{concept}.json")

        @app.get("/api/health")
        def health():
            return database.resource("health.json")

        @app.get("/data/{resource:path}")
        def data_resource(resource: str):
            # Download links and optional prerender assets share the same origin.
            # StaticFiles resolves containment itself; never read arbitrary paths.
            try:
                return database.resource(resource)
            except KeyError:
                target = (static / "data" / resource).resolve()
                if not target.is_relative_to(static / "data") or not target.is_file():
                    raise HTTPException(status_code=404, detail="Resource not found") from None
                from fastapi.responses import FileResponse

                return FileResponse(target)

    # Routes above must be mounted first. No API is silently emulated in static mode.
    app.mount("/", StaticFiles(directory=static, html=True), name="static")
    return app


def serve(
    static: Path, db: Path | None = None, *, host: str = "127.0.0.1", port: int = 8787
) -> None:
    """Start the optional local service, defaulting to the loopback interface."""
    app = create_app(static, db)
    import uvicorn

    uvicorn.run(app, host=host, port=port)
