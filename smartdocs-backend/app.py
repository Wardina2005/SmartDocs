"""Main FastAPI application entrypoint for SmartDocs Enterprise Document Management System."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes import router

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"

app = FastAPI(
    title="SmartDocs Enterprise Document Management System",
    version="1.0.0",
    description="Backend API for OCR document processing, persistence, and reporting.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    """Initialize upload directory and database schema when the service starts."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


app.include_router(router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, object]:
    """Return health status for the API service."""
    return {"status": "ok", "service": "smartdocs-backend"}
