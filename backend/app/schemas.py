from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ImportBatchRead(BaseModel):
    id: int
    import_type: str
    filename: str
    row_count: int
    created_at: datetime
    status: str

    class Config:
        from_attributes = True


class CanonicalProductRead(BaseModel):
    id: int
    canonical_name: str
    normalized_name: str | None = None
    primary_barcode: str | None = None
    primary_apn: str | None = None
    primary_pde: str | None = None
    review_status: str
    confidence_summary: str | None = None

    class Config:
        from_attributes = True


class SourceProductRead(BaseModel):
    id: int
    title: str
    handle: str | None = None
    sku: str | None = None
    barcode: str | None = None
    apn: str | None = None
    pde: str | None = None
    status: str | None = None

    class Config:
        from_attributes = True


class LinkReviewRead(BaseModel):
    id: int
    link_status: str
    link_method: str
    confidence_score: float | None = None
    fuzzy_score: float | None = None
    ai_score: float | None = None
    ai_reason: str | None = None
    locked: bool
    excluded: bool
    review_notes: str | None = None
    source_product: SourceProductRead
    canonical_product: CanonicalProductRead

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    canonical_products: int
    linked_shopify_products: int
    linked_fos_products: int
    unresolved_links: int
    conflicts: int
    reconciliation_ready: int
    import_batches: int
    export_runs: int


class ReviewActionRequest(BaseModel):
    action: str
    note: str | None = None
    canonical_product_id: int | None = None
    locked: bool | None = None


class ImportPreviewRow(BaseModel):
    row_number: int
    data: dict[str, Any]


class ImportPreviewResponse(BaseModel):
    detected_type: str
    columns: list[str]
    preview_rows: list[ImportPreviewRow]
    missing_columns: list[str]
    extra_columns: list[str]
