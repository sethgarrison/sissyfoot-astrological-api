from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from astrology.routers import chart_router, data_router
from core.db import init_db
from tarot.routers import api_router as tarot_api_router

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
}


async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title="Natal Chart API",
        description=(
            "Natal charts (Swiss Ephemeris / Kerykeion), interpretation data, and related APIs "
            "(e.g. tarot)."
        ),
        version="1.0.0",
    )

    app.include_router(chart_router)
    app.include_router(data_router)
    app.include_router(tarot_api_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def add_cors_to_exceptions(request, exc):
        if isinstance(exc, HTTPException):
            raise exc
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers=CORS_HEADERS,
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
