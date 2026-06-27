"""Fraud Detection API application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.transactions import router as transactions_router
from app.api.auth import router as auth_router
from app.api.analytics import router as analytics_router
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
        "Production-quality fraud detection API with a hybrid ML + rule-based engine."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for convenient portfolio deployment/access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions_router)
app.include_router(auth_router)
app.include_router(analytics_router)


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
