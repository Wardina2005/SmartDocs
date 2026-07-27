"""OCR processing pipeline for PDFs and images using EasyOCR with preprocessing."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from parser import parse_extracted_text

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover - optional dependency guard
    cv2 = None
    np = None

try:
    import easyocr  # type: ignore
except ImportError:  # pragma: no cover - optional dependency guard
    easyocr = None

try:
    from pdf2image import convert_from_path  # type: ignore
except ImportError:  # pragma: no cover - optional dependency guard
    convert_from_path = None


def preprocess_image(image: Image.Image) -> Image.Image:
    """Apply optional preprocessing before OCR to improve recognition quality."""
    if cv2 is not None and np is not None:
        image_np = np.array(image)
        if image_np.ndim == 2:
            gray = image_np
        else:
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        resized = cv2.resize(threshold, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        contrasted = cv2.convertScaleAbs(resized, alpha=1.2, beta=10)
        return Image.fromarray(contrasted)
    return image.convert("L")


def extract_text_from_image(image_path: Path) -> str:
    """Extract OCR text from a single image file."""
    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    processed = preprocess_image(image)

    if easyocr is None:
        return ""

    reader = easyocr.Reader(["en", "id"], gpu=False)
    results = reader.readtext(processed, detail=0, paragraph=False)
    return "\n".join(results)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Convert each PDF page to an image and extract OCR text from each page."""
    if convert_from_path is None:
        return ""
    pages = convert_from_path(pdf_path, dpi=300)
    extracted_chunks: list[str] = []
    for index, page in enumerate(pages):
        page_path = pdf_path.with_suffix(f"_{index + 1}.png")
        page.save(page_path, "PNG")
        extracted_chunks.append(extract_text_from_image(page_path))
        page_path.unlink(missing_ok=True)
    return "\n".join(extracted_chunks)


def process_document(file_path: Path, filename: str) -> dict[str, Any]:
    """Run OCR on the uploaded file and return parsed structured data."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        extracted_text = extract_text_from_pdf(file_path)
    elif suffix in {".png", ".jpg", ".jpeg", ".bmp"}:
        extracted_text = extract_text_from_image(file_path)
    else:
        raise ValueError("Unsupported file type")

    parsed = parse_extracted_text(extracted_text, filename)
    return {
        "success": True,
        "data": {
            "vendor": parsed.get("vendor", ""),
            "invoice_number": parsed.get("invoice_number", ""),
            "invoice_date": parsed.get("invoice_date", ""),
            "activity_name": parsed.get("activity_name", ""),
            "division": parsed.get("division", ""),
            "category": parsed.get("category", ""),
            "payment_method": parsed.get("payment_method", ""),
            "description": parsed.get("description", ""),
            "grand_total": parsed.get("grand_total", 0),
            "items": parsed.get("items", []),
            "ocr_text": extracted_text[:4000],
        },
    }
