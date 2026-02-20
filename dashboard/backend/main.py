"""
FastAPI application entry-point for the Algerie Post Tracking Dashboard.

Run with:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load heavy resources once on startup."""
    # Import here to avoid circular imports at module level
    from services.data_service import load_reference_data
    from services.ml_service import load_model

    load_reference_data()
    load_model()
    yield  # app is running
    # shutdown – nothing to clean up


app = FastAPI(
    title="Algerie Post Tracking API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
from routers import chat, export, predictions, stats  # noqa: E402

app.include_router(predictions.router)
app.include_router(stats.router)
app.include_router(chat.router)
app.include_router(export.router)


@app.get("/")
def root():
    return {"message": "Algerie Post Tracking API is running."}
