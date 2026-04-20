from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ImportBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    import_type: str
    filename: str
    row_count: int
    created_at: datetime
    status: str


class CanonicalProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name: str
    normalized_name: Optional[str] = None
    primary_barcode: Optional[str] = None
    primary_apn: Optional[str] = None
    primary_pde: Optional[str] = None
    review_status: str
    confidence_summary: Optional[str] = None


class SourceProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    external_variant_id: Optional[str] = None
    external_inventory_item_id: Optional[str] = None
    external_location_id: Optional[str] = None
    source_location_name: Optional[str] = None
    handle: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    apn: Optional[str] = None
    pde: Optional[str] = None
    status: Optional[str] = None


class LinkReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    link_status: str
    link_method: str
    confidence_score: Optional[float] = None
    fuzzy_score: Optional[float] = None
    ai_score: Optional[float] = None
    ai_reason: Optional[str] = None
    locked: bool
    excluded: bool
    review_notes: Optional[str] = None
    source_product: SourceProductRead
    canonical_product: CanonicalProductRead


class DashboardSummary(BaseModel):
    canonical_products: int
    linked_shopify_products: int
    linked_fos_products: int
    unresolved_links: int
    conflicts: int
    reconciliation_ready: int
    import_batches: int
    export_runs: int
    legacy_duplicate_groups: int = 0
    legacy_duplicate_records: int = 0


class ReviewActionRequest(BaseModel):
    action: str
    note: Optional[str] = None
    canonical_product_id: Optional[int] = None
    locked: Optional[bool] = None


class BulkReviewActionRequest(BaseModel):
    link_ids: List[int]
    action: str
    note: Optional[str] = None
    canonical_product_id: Optional[int] = None
    locked: Optional[bool] = None


class ImportPreviewRow(BaseModel):
    row_number: int
    data: Dict[str, Any]


class ImportPreviewResponse(BaseModel):
    detected_type: str
    columns: List[str]
    preview_rows: List[ImportPreviewRow]
    missing_columns: List[str]
    extra_columns: List[str]


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    limit: int
    offset: int
