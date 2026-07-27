"""Text parsing helpers for OCR output into structured invoice fields."""
from __future__ import annotations

import re
from typing import Any


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and normalize common OCR issues."""
    return re.sub(r"\s+", " ", text or "").strip()


def _find_first(pattern: str, text: str) -> str:
    """Return the first regex match or an empty string."""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match and match.lastindex else ""


def _find_currency_amount(text: str) -> float:
    """Extract the most relevant currency amount from OCR text."""
    matches = re.findall(r"(?:\$|Rp|USD|IDR|SAR|EUR)\s*([0-9,]+(?:\.\d{1,2})?)", text)
    if not matches:
        return 0.0
    numbers = [float(value.replace(",", "")) for value in matches]
    return max(numbers) if numbers else 0.0


def extract_vendor(text: str) -> str:
    """Infer a vendor name from the OCR text."""
    candidates = [
        _find_first(r"(?:vendor|from)[:\s]+([A-Za-z0-9&.\- /]+)", text),
        _find_first(r"([A-Z][A-Za-z0-9&.\- /]{3,40})", text),
    ]
    return next((item for item in candidates if item), "")


def extract_invoice_number(text: str) -> str:
    """Extract an invoice number using common invoice labels."""
    patterns = [
        r"(?:invoice\s*(?:no|number)|inv\s*no|no\.?\s*invoice)[:\s#-]*([A-Za-z0-9\-\/]+)",
        r"(?:invoice)\s*([A-Za-z0-9\-\/]{2,20})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def extract_invoice_date(text: str) -> str:
    """Extract an invoice date from OCR text using common date patterns."""
    patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{2}-\d{2}-\d{4})",
        r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def detect_division(text: str) -> str:
    """Map detected terms to a standard division label."""
    lowered = text.lower()
    if "finance" in lowered or "account" in lowered:
        return "Finance"
    if "legal" in lowered:
        return "Legal"
    if "it" in lowered or "technology" in lowered:
        return "Technology"
    if "operation" in lowered:
        return "Operations"
    return "General"


def detect_category(text: str) -> str:
    """Infer the best document category from OCR text."""
    lowered = text.lower()
    if "invoice" in lowered:
        return "Invoice"
    if "receipt" in lowered:
        return "Receipt"
    if "purchase" in lowered:
        return "Purchase"
    return "Document"


def detect_payment_method(text: str) -> str:
    """Detect payment method from OCR text."""
    lowered = text.lower()
    if "bank transfer" in lowered or "transfer" in lowered:
        return "Bank Transfer"
    if "credit card" in lowered or "card" in lowered:
        return "Credit Card"
    if "cash" in lowered:
        return "Cash"
    return "TBD"


def extract_description(text: str) -> str:
    """Create a concise description from the OCR text."""
    text = normalize_whitespace(text)
    if not text:
        return "OCR extracted document"
    return text[:220]


def extract_items(text: str) -> list[dict[str, Any]]:
    """Infer a simple item table from OCR lines when possible."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    items: list[dict[str, Any]] = []
    for line in lines:
        if re.search(r"\b(?:qty|quantity|price|total)\b", line.lower()):
            continue
        if re.search(r"\b(?:invoice|date|vendor|payment|due|total)\b", line.lower()):
            continue
        if len(line.split()) < 3:
            continue
        parts = re.split(r"\s{2,}", line)
        if len(parts) >= 2:
            item_name = parts[0][:80]
            qty = 1
            price = 0.0
            total = 0.0
            if len(parts) >= 2 and re.search(r"\d", parts[-1]):
                total = float(re.sub(r"[^0-9.]", "", parts[-1]))
            items.append({"item": item_name, "qty": qty, "price": price, "total": total})
            if len(items) >= 5:
                break
    if not items:
        items.append({"item": "Extracted Item", "qty": 1, "price": 0.0, "total": 0.0})
    return items


def parse_extracted_text(text: str, filename: str = "") -> dict[str, Any]:
    """Parse OCR text into the structured payload expected by the frontend."""
    normalized = normalize_whitespace(text)
    vendor = extract_vendor(normalized) or filename.replace(".", " ").title()
    invoice_number = extract_invoice_number(normalized)
    invoice_date = extract_invoice_date(normalized)
    grand_total = _find_currency_amount(normalized)
    items = extract_items(normalized)
    return {
        "vendor": vendor,
        "invoice_number": invoice_number or "INV-001",
        "invoice_date": invoice_date or "",
        "activity_name": "OCR Processed Document",
        "division": detect_division(normalized),
        "category": detect_category(normalized),
        "payment_method": detect_payment_method(normalized),
        "description": extract_description(normalized),
        "grand_total": grand_total,
        "items": items,
    }
