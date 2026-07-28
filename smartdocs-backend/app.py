"""Main FastAPI application entrypoint for SmartDocs Enterprise Document Management System."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles

from database import init_db
from routes import router

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
FRONTEND_DIR = BASE_DIR.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize upload directory and database schema when the service starts."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title="SmartDocs Enterprise Document Management System",
    version="1.0.0",
    description="Backend API for OCR document processing, persistence, and reporting.",
    lifespan=lifespan,
)

# Konfigurasi CORS agar frontend dapat berkomunikasi dengan backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

print("\n===== REGISTERED ROUTES =====")
for route in app.routes:
    print(route.path)
print("=============================\n")

@app.get("/health")
def health_check() -> dict[str, object]:
    """Return health status for the API service."""
    return {"status": "ok", "service": "smartdocs-backend"}


# Mount static files untuk melayani frontend HTML/CSS/JS dari folder root
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
