"""Pydantic models used by the SmartDocs API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class OCRItem(BaseModel):
    """Represents an extracted invoice item."""

    item: str = Field(default="")
    qty: float = Field(default=0.0)
    price: float = Field(default=0.0)
    total: float = Field(default=0.0)


class OCRResponse(BaseModel):
    """Structured OCR extraction payload returned to the frontend."""

    vendor: str = Field(default="")
    invoice_number: str = Field(default="")
    invoice_date: str = Field(default="")
    activity_name: str = Field(default="")
    division: str = Field(default="")
    category: str = Field(default="")
    payment_method: str = Field(default="")
    description: str = Field(default="")
    grand_total: float = Field(default=0.0)
    items: list[OCRItem] = Field(default_factory=list)


class SaveDocumentPayload(OCRResponse):
    """Document payload accepted by the persistence endpoint."""

    pass
