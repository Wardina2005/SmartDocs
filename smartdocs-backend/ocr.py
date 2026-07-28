"""OCR processing pipeline for PDFs and images using EasyOCR with dynamic extraction."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

# pyrefly: ignore [missing-import]
from PIL import Image, ImageOps

from parser import parse_extracted_text

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except ImportError:
    cv2 = None
    np = None

try:
    import easyocr  # type: ignore
except ImportError:
    easyocr = None

try:
    from pdf2image import convert_from_path  # type: ignore
except ImportError:
    convert_from_path = None

# Global reader instance untuk menghindari re-initialization berulang
EASYOCR_READER = None


def get_ocr_reader():
    """Mendapatkan atau menginisialisasi singleton instance EasyOCR Reader."""
    global EASYOCR_READER
    if EASYOCR_READER is None and easyocr is not None:
        try:
            # Gunakan model Indonesia ('id') dan Inggris ('en') untuk pengenalan kata presisi
            EASYOCR_READER = easyocr.Reader(["id", "en"], gpu=False, verbose=False)
        except Exception as err:
            print(f"[EasyOCR Init 'id,en' Error, falling back to 'en'] {err}")
            try:
                EASYOCR_READER = easyocr.Reader(["en"], gpu=False, verbose=False)
            except Exception as err2:
                print(f"[EasyOCR Init Error] {err2}")
    return EASYOCR_READER


def preprocess_image(image: Image.Image) -> Image.Image:
    """Pertajam gambar tanpa menimbulkan noise berlebihan pada teks halus."""
    w, h = image.size
    if w < 1800:
        scale = 1800.0 / float(w)
        new_w, new_h = int(w * scale), int(h * scale)
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if cv2 is not None and np is not None:
        img_np = np.array(image.convert("RGB"))
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # Gunakan CLAHE halus untuk meningkatkan kontras teks
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        return Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB))

    return image.convert("RGB")


def extract_text_from_image(image_path: Path | str) -> str:
    """Extract OCR text from a single image file with precise bounding box line grouping."""
    try:
        path = Path(image_path) if isinstance(image_path, str) else image_path
        image = Image.open(path)
        image = ImageOps.exif_transpose(image)

        reader = get_ocr_reader()
        if reader is None:
            return ""

        # Resize gambar ke resolusi tinggi bersih
        w, h = image.size
        if w < 1800:
            scale = 1800.0 / float(w)
            new_w, new_h = int(w * scale), int(h * scale)
            img_resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            img_resized = image

        img_np = np.array(img_resized.convert("RGB"))

        # Jalankan OCR dengan mag_ratio=1.5 untuk deteksi font tabel lebih jelas
        results = reader.readtext(img_np, detail=1, paragraph=False, mag_ratio=1.5)

        if not results:
            processed_img = preprocess_image(image)
            img_np = np.array(processed_img)
            results = reader.readtext(img_np, detail=1, paragraph=False, mag_ratio=1.5)

        if not results:
            return ""

        boxes = []
        for bbox, text, prob in results:
            text_str = str(text).strip()
            if not text_str or prob < 0.12:
                continue
            x_min = min(pt[0] for pt in bbox)
            x_max = max(pt[0] for pt in bbox)
            y_min = min(pt[1] for pt in bbox)
            y_max = max(pt[1] for pt in bbox)
            y_center = (y_min + y_max) / 2.0
            height = max(y_max - y_min, 10.0)
            boxes.append({
                "text": text_str,
                "x_min": x_min,
                "x_max": x_max,
                "y_min": y_min,
                "y_max": y_max,
                "y_center": y_center,
                "height": height,
                "prob": prob,
            })

        if not boxes:
            return ""

        # Urutkan secara vertikal dari atas ke bawah
        boxes.sort(key=lambda b: b["y_center"])

        # Pengelompokkan baris presisi berdasarkan toleransi tinggi font
        lines_out = []
        current_line = []

        for box in boxes:
            if not current_line:
                current_line.append(box)
            else:
                line_y_avg = sum(b["y_center"] for b in current_line) / float(len(current_line))
                avg_h = sum(b["height"] for b in current_line) / float(len(current_line))

                # Toleransi Y ketat (maksimal 45% tinggi font atau 10px)
                if abs(box["y_center"] - line_y_avg) <= max(8.0, avg_h * 0.45):
                    current_line.append(box)
                else:
                    current_line.sort(key=lambda b: b["x_min"])
                    lines_out.append("  ".join(b["text"] for b in current_line))
                    current_line = [box]

        if current_line:
            current_line.sort(key=lambda b: b["x_min"])
            lines_out.append("  ".join(b["text"] for b in current_line))

        return "\n".join(lines_out)
    except Exception as e:
        print(f"[OCR Extract Image Error] {e}")
        return ""


def extract_text_from_pdf(pdf_path: Path | str) -> str:
    """Convert each PDF page to an image and extract OCR text from each page."""
    if convert_from_path is None:
        return ""

    path = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path
    try:
        pages = convert_from_path(path, dpi=300)
        extracted_chunks: list[str] = []
        for index, page in enumerate(pages):
            page_path = path.with_suffix(f"_{index + 1}.png")
            page.save(page_path, "PNG")
            extracted_chunks.append(extract_text_from_image(page_path))
            page_path.unlink(missing_ok=True)
        return "\n".join(extracted_chunks)
    except Exception as e:
        print(f"[OCR Extract PDF Error] {e}")
        return ""


def extract_table_items_from_text(raw_text: str) -> List[Dict[str, Any]]:
    """Fallback table extraction logic for OCR text."""
    items: List[Dict[str, Any]] = []
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    strict_ignore = [
        "subtotal", "grand total", "total pembayaran", "total belanja", "total bayar",
        "ppn", "pph", "wire to", "bank", "an.", "acount", "account", "cabang",
        "catatan", "terima kasih", "nomor induk berusaha"
    ]

    for index, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in strict_ignore):
            break

        amount_matches = re.findall(r"(?:rp\.??\s*)?(?<!\d)(\d{1,3}(?:[.,]\d{3})+|\d+)(?!\d)", line, re.IGNORECASE)
        if not amount_matches:
            continue

        amounts = []
        for match in amount_matches:
            cleaned = re.sub(r"[^\d]", "", match)
            if cleaned:
                amounts.append(int(cleaned))

        if not amounts:
            continue

        item_name = re.sub(r"(?:rp\.??\s*)?(?<!\d)(\d{1,3}(?:[.,]\d{3})+|\d+)(?!\d)", " ", line, flags=re.IGNORECASE)
        item_name = re.sub(r"[^a-zA-Z0-9\s\-/]", " ", item_name)
        item_name = re.sub(r"\s+", " ", item_name).strip(" -:,;")
        item_name = re.sub(r"^\d+\s+", "", item_name).strip()

        if not item_name or len(item_name) < 2:
            continue

        qty = 1
        if len(amounts) >= 2 and amounts[0] < 100:
            qty = amounts[0]

        price = max(amounts)
        total = price * qty if qty > 1 else price
        items.append({
            "item": item_name.title(),
            "qty": qty,
            "price": price,
            "total": total,
        })

    return items


def process_document(file_path: Path | str, filename: str) -> Dict[str, Any]:
    """Run OCR on the uploaded file and return parsed structured data dynamically."""
    path = Path(file_path) if isinstance(file_path, str) else file_path
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        extracted_text = extract_text_from_pdf(path)
    else:
        extracted_text = extract_text_from_image(path)

    print("=== RAW OCR TEXT ===")
    print(extracted_text)

    parsed = {}
    try:
        parsed = parse_extracted_text(extracted_text, filename)
    except Exception as parse_err:
        print(f"[Parser Error] {parse_err}")

    if not isinstance(parsed, dict):
        parsed = {}

    items = parsed.get("items", [])
    if not items:
        items = extract_table_items_from_text(extracted_text)

    grand_total = parsed.get("grand_total", 0)
    try:
        grand_total = float(grand_total)
    except (ValueError, TypeError):
        grand_total = 0.0

    if grand_total == 0 and items:
        grand_total = sum(float(item.get("total", 0)) for item in items if isinstance(item, dict))

    return {
        "success": True,
        "data": {
            "vendor": parsed.get("vendor") or "Unknown Vendor",
            "invoice_number": parsed.get("invoice_number") or "-",
            "invoice_date": parsed.get("invoice_date") or "-",
            "activity_name": parsed.get("activity_name") or "-",
            "division": parsed.get("division") or "General",
            "category": parsed.get("category") or "-",
            "payment_method": parsed.get("payment_method") or "Cash / Transfer",
            "description": parsed.get("description") or "-",
            "grand_total": grand_total,
            "items": items,
            "ocr_text": extracted_text[:4000] if extracted_text else "",
        },
    }