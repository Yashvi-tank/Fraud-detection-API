"""Fraud Detection API application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app.api.transactions import router as transactions_router
from app.core.config import settings
from app.core.database import init_db
from app.utils.logging import setup_logging


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize resources on startup and clean up on shutdown."""
    setup_logging(debug=settings.DEBUG)
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-quality fraud detection API with a rule-based engine. "
        "Designed for future integration with JWT auth, Redis caching, "
        "device/country tracking, and ML-based prediction."
    ),
    lifespan=lifespan,
)

app.include_router(transactions_router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Verify that the API is running.",
)
def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(status="healthy")
