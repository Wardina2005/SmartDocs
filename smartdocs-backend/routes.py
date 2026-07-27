"""API routes for OCR processing, persistence, and reporting."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from database import get_activity_logs, get_dashboard_stats, get_documents, get_reports_data, save_document
from models import OCRResponse, SaveDocumentPayload
from ocr import process_document
from utils import clean_filename, save_upload_file

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """Accept an uploaded document and persist it temporarily on disk."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    save_path = save_upload_file(file)
    return JSONResponse(status_code=200, content={"success": True, "file_path": str(save_path), "filename": file.filename})


@router.post("/scan", response_model=OCRResponse)
async def scan_document(file: UploadFile = File(...)) -> JSONResponse:
    """Run OCR on the uploaded file and return structured data to the frontend."""
    try:
        if not file.filename:
            raise ValueError("No file selected")

        save_path = save_upload_file(file)
        result = process_document(save_path, clean_filename(file.filename))
        return JSONResponse(status_code=200, content={"success": True, "data": result["data"]})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {exc}") from exc


@router.post("/save")
async def save_document_route(payload: SaveDocumentPayload) -> JSONResponse:
    """Save OCR results to MySQL and return the stored document identifier."""
    try:
        document_id = save_document(payload.model_dump())
        return JSONResponse(status_code=200, content={"success": True, "document_id": document_id})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database save failed: {exc}") from exc


@router.get("/documents")
def list_documents() -> JSONResponse:
    """Return all persisted documents for the repository page."""
    return JSONResponse(status_code=200, content={"success": True, "documents": get_documents()})


@router.get("/dashboard")
def dashboard_stats() -> JSONResponse:
    """Return dashboard statistics for the analytics page."""
    return JSONResponse(status_code=200, content={"success": True, "data": get_dashboard_stats()})


@router.get("/reports")
def reports_stats() -> JSONResponse:
    """Return reporting aggregates for the reports page."""
    return JSONResponse(status_code=200, content={"success": True, "data": get_reports_data()})


@router.get("/activity")
def activity_logs() -> JSONResponse:
    """Return recent activity entries for the audit log page."""
    return JSONResponse(status_code=200, content={"success": True, "data": get_activity_logs()})
