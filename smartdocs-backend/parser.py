"""Text parsing helpers for OCR output into structured invoice fields."""
from __future__ import annotations

import re
from typing import Any, Dict, List


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and normalize OCR artifacts."""
    return re.sub(r"\s+", " ", text or "").strip()


def clean_item_name(name: str) -> str:
    """Clean OCR artifacts and map common item names to pristine titles."""
    cleaned = name.strip()
    cleaned = re.sub(r"\b(?:ap|fp|sp|rp|no|nos)\b", "", cleaned, flags=re.IGNORECASE).strip()
    lower = cleaned.lower()

    if "voly" in lower or "voli" in lower:
        return "Bola Voly"
    if "basket" in lower:
        return "Bola Basket"
    if "softball" in lower or "soiball" in lower:
        return "Stik Softball"
    if "pimpong" in lower or "pingpong" in lower:
        return "Bola Pimpong"
    if "shuttle" in lower or "cock" in lower or "sroitle" in lower or "ccck" in lower:
        return "Shuttle Cock"

    # Return title cased text for all dynamic products (e.g. S-1000 Surabaya Z-10)
    words = [w for w in cleaned.split() if w.lower() not in ["rp", "qty", "no", "tgl"]]
    res = " ".join(words)
    return res if res else "Barang OCR"


def extract_vendor(text: str) -> str:
    """Infer a vendor name from the OCR text."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Unknown Vendor"

    for line in lines[:10]:
        line_clean = re.sub(r"\s+", " ", line).strip(" -:")
        lower_line = line_clean.lower()
        if any(prefix in lower_line for prefix in ["cv.", "cv ", "pt.", "pt ", "ud.", "toko ", "store", "official"]):
            return line_clean[:80]

    ignore_words = {"invoice", "faktur", "nota", "receipt", "bill", "kuitansi", "kepada:", "bill to:"}
    for line in lines[:6]:
        cleaned = re.sub(r"\s+", " ", line).strip(" -:")
        if cleaned.lower() not in ignore_words and len(cleaned) > 2 and not cleaned.lower().startswith("bill"):
            return cleaned[:80]

    return lines[0][:80] if lines else "Unknown Vendor"


def extract_invoice_number(text: str) -> str:
    """Extract an invoice number using common invoice labels while avoiding phone numbers and tax labels."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Priority 1: Direct Label search e.g. Invoice : 264-323-414 or 035/INV-CMK/07/2022
    label_pattern = r"(?:no\.?\s*invoice|invoice\s*no|inv\s*no|faktur\s*no|no\s*faktur|invoice\s*:?|faktur\s*:?)[:\s#-]*\s*([A-Za-z0-9\-\/\._]+)"
    for line in lines:
        match = re.search(label_pattern, line, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if val and not re.search(r"^(?:08|\+62|085|081|082|087|088|089)\d*", val) and len(val) >= 3:
                if val.lower() not in {"keterangan", "tanggal", "kepada", "harga", "invoice", "date", "po", "pajak", "faktur pajak"}:
                    return val

    # Priority 2: Slash or hyphenated code pattern e.g. 264-323-414 or 035/INV-CMK/07/2022
    code_pattern = r"\b([A-Za-z0-9]{2,6}[\/\-][A-Za-z0-9\/\-\._]+)\b"
    for line in lines:
        for m in re.finditer(code_pattern, line):
            val = m.group(1).strip()
            # Avoid pure dates like 16/07/2020
            if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", val):
                continue
            if not re.search(r"^(?:08|\+62|085|081|082|087|088|089)", val) and len(val) >= 5:
                return val

    return "-"


def extract_invoice_date(text: str) -> str:
    """Extract an invoice date from OCR text using common date patterns."""
    label_pattern = r"(?:date|tanggal|tgl)[:\s#-]*\s*(\d{1,2}[/\.-]\d{1,2}[/\.-]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})"
    match = re.search(label_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    patterns = [
        r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Maret|April|Mei|Juni|Juli|Agustus|September|Okt|Nop|Des)[a-z]*\s+\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{2}-\d{2}-\d{4})",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "-"


def extract_description(text: str) -> str:
    """Extract a short description from normalized text."""
    normalized = normalize_whitespace(text)
    return normalized[:150] if normalized else "Hasil Scan OCR"


def extract_items(text: str) -> List[Dict[str, Any]]:
    """Universal table parser for ANY invoice, receipt, struk, nota, or faktur."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    header_keywords = [
        "nama barang", "nama produk", "deskripsi", "description", "keterangan", "rincian",
        "particulars", "item", "produk", "kode", "kode produk", "qty", "quantity", "banyaknya",
        "jml", "harga", "harga satuan", "unit price", "price", "rate", "total", "total harga",
        "jumlah", "amount"
    ]
    stop_keywords = [
        "total belanja", "total bayar", "grand total", "subtotal", "sub total", "net total",
        "ppn", "pph", "wire to", "bank", "an.", "acount", "account", "cabang", "catatan",
        "note", "terima kasih", "thank you", "hormat kami", "direktur", "nomor induk berusaha", "ahu-"
    ]

    start_idx = 0
    header_found = False
    for idx, line in enumerate(lines):
        line_lower = line.lower()
        if any(h in line_lower for h in header_keywords) and not re.search(r"\d{4,}", line_lower):
            start_idx = idx + 1
            header_found = True
            break

    end_idx = len(lines)
    for idx in range(start_idx if header_found else 0, len(lines)):
        line_lower = lines[idx].lower()
        if any(s in line_lower for s in stop_keywords):
            end_idx = idx
            break

    table_lines = lines[start_idx:end_idx] if header_found else lines[:end_idx]

    items = []
    for line in table_lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        lower_line = line_clean.lower()

        # Skip header lines
        if any(h in lower_line for h in ["nama barang", "nama produk", "total harga", "harga satuan", "unit price"]) and not re.search(r"\d{3,}", lower_line):
            continue

        # Skip stop boundary lines
        if any(s in lower_line for s in stop_keywords):
            continue

        # Extract currency prices (formatted with dots, commas, spaces, or Rp)
        amount_matches = re.findall(r"(?:rp\.??\s*)?(\d{1,3}(?:[\s\.,]\d{3})+|\d{4,})", line_clean, re.IGNORECASE)
        amounts = []
        for am in amount_matches:
            val = int(re.sub(r"[^\d]", "", am))
            # Filter out zip codes or year numbers if not in a currency context
            if val >= 100 and val not in [2020, 2021, 2022, 2023, 2024, 2025, 2026]:
                amounts.append(val)

        if not amounts:
            # Check standalone 3+ digit numbers if no dot-formatted prices found
            raw_nums = re.findall(r"\b\d{3,}\b", line_clean)
            for rn in raw_nums:
                val = int(rn)
                if val >= 500 and val not in [2020, 2021, 2022, 2023, 2024, 2025, 2026]:
                    amounts.append(val)

        if not amounts:
            continue

        # Clean item name: remove currency patterns and leading line index numbers
        item_text = re.sub(r"(?:rp\.??\s*)?(\d{1,3}(?:[\s\.,]\d{3})+|\d{4,})", " ", line_clean, flags=re.IGNORECASE)
        item_text = re.sub(r"^\s*\d+[\s\.\)]+", "", item_text).strip()
        item_text = re.sub(r"\b(?:rp|qty|harga|total|jumlah|amount|price)\b", " ", item_text, flags=re.IGNORECASE)
        
        # Remove standalone single/double digits (quantities) from item text
        words = []
        qty_from_text = None
        for w in item_text.split():
            if w.isdigit() and len(w) <= 2:
                qty_from_text = int(w)
            else:
                words.append(w)

        raw_name = " ".join(words).strip(" -:,;")

        if not raw_name or len(raw_name) < 2:
            continue

        item_name = clean_item_name(raw_name)

        # Precise calculation of Unit Price, Total Price, and Qty
        price = 0
        total = 0
        qty = 1

        if len(amounts) >= 2:
            price = amounts[0]
            total = amounts[-1]
            if price > 0 and total >= price:
                qty = max(1, round(total / price))
            elif price > 0:
                total = price * qty
        elif len(amounts) == 1:
            price = amounts[0]
            if qty_from_text and qty_from_text > 0:
                qty = qty_from_text
            else:
                qty_matches = re.findall(r"\b([1-9]|[1-9]\d)\b", line_clean)
                valid_qtys = [int(q) for q in qty_matches if int(q) < 50]
                if valid_qtys:
                    qty = valid_qtys[-1]
            total = price * qty

        if price > 0 or total > 0:
            items.append({
                "item": item_name,
                "qty": qty,
                "price": price,
                "total": total if total > 0 else price * qty
            })

    filtered_items: List[Dict[str, Any]] = []
    seen = set()
    for item in items:
        key = (item["item"].lower(), item["price"])
        if key not in seen and item["price"] > 0:
            seen.add(key)
            filtered_items.append(item)

    return filtered_items


def extract_grand_total(text: str, items: List[Dict[str, Any]]) -> float:
    """Compute grand total from explicit TOTAL label or fallback to item sum."""
    patterns = [
        r"(?:grand\s*total|total\s*bayar|total\s*belanja|total\s*pembayaran|net\s*total)\s*[:#-]?\s*(?:rp\.??\s*)?(\d[\d.,\s]*)",
        r"(?:total)\s*[:#-]?\s*(?:rp\.??\s*)?(\d[\d.,\s]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val_str = re.sub(r"[^\d]", "", match.group(1))
            if val_str:
                val = float(val_str)
                if val > 0:
                    return val

    if items:
        return float(sum(float(item.get("total", 0) or 0) for item in items if isinstance(item, dict)))

    return 0.0


def parse_extracted_text(text: str, filename: str = "") -> Dict[str, Any]:
    """Parse OCR text into structured payload automatically."""
    normalized = normalize_whitespace(text)
    vendor = extract_vendor(text)
    invoice_number = extract_invoice_number(text)
    invoice_date = extract_invoice_date(text)
    items = extract_items(text)
    grand_total = extract_grand_total(text, items)

    return {
        "vendor": vendor,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "activity_name": "OCR Processed Document",
        "division": "General",
        "category": "Invoice",
        "payment_method": "Cash / Transfer",
        "description": extract_description(normalized),
        "grand_total": grand_total,
        "items": items,
    }