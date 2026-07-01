from opensearchpy.exceptions import ConnectionError, TransportError

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AskOFF Search API",
        version="0.1.0",
        description="Search and retrieval API for Canadian Open Food Facts products",
    )

    @app.exception_handler(ConnectionError)
    @app.exception_handler(TransportError)
    async def opensearch_error_handler(
        request: Request, exc: ConnectionError | TransportError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "error": "search_engine_unavailable",
                "detail": (
                    "Could not connect to OpenSearch. "
                    "Ensure OpenSearch is running on localhost:9200."
                ),
            },
        )

    app.include_router(router)
    return app


app = create_app()
