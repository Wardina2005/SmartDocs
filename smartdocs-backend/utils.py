"""Utility helpers for file handling and input normalization."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import UploadFile

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"


def clean_filename(filename: str) -> str:
    """Return a safe, normalized filename for storage and processing."""
    return Path(filename).name.replace(" ", "_")


def save_upload_file(upload: UploadFile) -> Path:
    """Save a temporary uploaded file to the backend uploads directory."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_name = clean_filename(upload.filename or "upload.bin")
    file_path = UPLOAD_DIR / file_name
    with file_path.open("wb") as destination:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            destination.write(chunk)
    return file_path
