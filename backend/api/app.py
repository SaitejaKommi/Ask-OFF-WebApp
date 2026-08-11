from opensearchpy.exceptions import ConnectionError, TransportError

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from config.settings import settings


from contextlib import asynccontextmanager

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from query.dictionaries import load_dynamic_dictionaries
        load_dynamic_dictionaries()
        yield

    app = FastAPI(
        title="Search Platform API",
        version="0.2.0",
        description="Search and retrieval API for search products",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ConnectionError)
    async def opensearch_connection_error_handler(
        request: Request, exc: ConnectionError
    ) -> JSONResponse:
        hosts_str = ", ".join(settings.opensearch_hosts)
        return JSONResponse(
            status_code=503,
            content={
                "error": "search_engine_unavailable",
                "detail": (
                    f"Could not connect to OpenSearch. "
                    f"Ensure OpenSearch is running on {hosts_str}."
                ),
            },
        )

    @app.exception_handler(TransportError)
    async def opensearch_transport_error_handler(
        request: Request, exc: TransportError
    ) -> JSONResponse:
        status_code = exc.status_code if isinstance(exc.status_code, int) else 500
        out_status = status_code if 400 <= status_code < 500 else 503

        return JSONResponse(
            status_code=out_status,
            content={
                "error": (
                    "search_engine_error"
                    if out_status == 400
                    else "search_engine_unavailable"
                ),
                "detail": f"Database returned error status {status_code}: {exc.error}",
            },
        )

    app.include_router(router)
    return app


app = create_app()

