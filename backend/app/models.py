from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CanonicalProduct(Base, TimestampMixin):
    __tablename__ = 'canonical_products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(512), index=True)
    normalized_name: Mapped[str | None] = mapped_column(String(512), index=True)
    preferred_brand: Mapped[str | None] = mapped_column(String(255))
    preferred_form: Mapped[str | None] = mapped_column(String(255))
    preferred_strength: Mapped[str | None] = mapped_column(String(255))
    preferred_pack_size: Mapped[str | None] = mapped_column(String(255))
    primary_barcode: Mapped[str | None] = mapped_column(String(64), index=True)
    primary_apn: Mapped[str | None] = mapped_column(String(64), index=True)
    primary_pde: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(64), default='ACTIVE')
    review_status: Mapped[str] = mapped_column(String(64), default='NEEDS_REVIEW')
    notes: Mapped[str | None] = mapped_column(Text)
    created_from_source: Mapped[str | None] = mapped_column(String(64))
    confidence_summary: Mapped[str | None] = mapped_column(Text)


class SourceSystem(Base):
    __tablename__ = 'source_systems'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))


class ImportBatch(Base):
    __tablename__ = 'import_batches'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_type: Mapped[str] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    file_hash: Mapped[str | None] = mapped_column(String(128))
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default='IMPORTED')


class SourceProduct(Base):
    __tablename__ = 'source_products'
    __table_args__ = (UniqueConstraint('source_system_id', 'source_record_key', name='uq_source_record'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_system_id: Mapped[int] = mapped_column(ForeignKey('source_systems.id'), index=True)
    source_record_key: Mapped[str] = mapped_column(String(255))
    external_product_id: Mapped[str | None] = mapped_column(String(255))
    handle: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    normalized_title: Mapped[str | None] = mapped_column(String(512), index=True)
    sku: Mapped[str | None] = mapped_column(String(128), index=True)
    barcode: Mapped[str | None] = mapped_column(String(128), index=True)
    apn: Mapped[str | None] = mapped_column(String(128), index=True)
    pde: Mapped[str | None] = mapped_column(String(128), index=True)
    vendor: Mapped[str | None] = mapped_column(String(255))
    product_type: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(64))
    raw_payload_json: Mapped[dict | None] = mapped_column(JSON)
    last_import_batch_id: Mapped[int | None] = mapped_column(ForeignKey('import_batches.id'))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProductIdentifier(Base):
    __tablename__ = 'product_identifiers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_product_id: Mapped[int] = mapped_column(ForeignKey('canonical_products.id'), index=True)
    identifier_type: Mapped[str] = mapped_column(String(64), index=True)
    identifier_value: Mapped[str] = mapped_column(String(128), index=True)
    normalized_identifier_value: Mapped[str] = mapped_column(String(128), index=True)
    source: Mapped[str | None] = mapped_column(String(64))
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SourceProductLink(Base, TimestampMixin):
    __tablename__ = 'source_product_links'
    __table_args__ = (UniqueConstraint('source_product_id', name='uq_source_product_link'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_product_id: Mapped[int] = mapped_column(ForeignKey('canonical_products.id'), index=True)
    source_product_id: Mapped[int] = mapped_column(ForeignKey('source_products.id'), index=True)
    link_status: Mapped[str] = mapped_column(String(64), index=True)
    link_method: Mapped[str] = mapped_column(String(64), index=True)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    fuzzy_score: Mapped[float | None] = mapped_column(Float)
    ai_score: Mapped[float | None] = mapped_column(Float)
    ai_reason: Mapped[str | None] = mapped_column(Text)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[str | None] = mapped_column(String(255))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    review_notes: Mapped[str | None] = mapped_column(Text)


class CandidateLink(Base):
    __tablename__ = 'candidate_links'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(128), index=True)
    source_product_id: Mapped[int] = mapped_column(ForeignKey('source_products.id'), index=True)
    candidate_canonical_product_id: Mapped[int | None] = mapped_column(ForeignKey('canonical_products.id'), index=True)
    candidate_source_product_id: Mapped[int | None] = mapped_column(ForeignKey('source_products.id'))
    candidate_rank: Mapped[int] = mapped_column(Integer)
    match_method: Mapped[str] = mapped_column(String(64))
    fuzzy_score: Mapped[float | None] = mapped_column(Float)
    ai_score: Mapped[float | None] = mapped_column(Float)
    ai_reason: Mapped[str | None] = mapped_column(Text)
    proposed_action: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InventorySnapshot(Base):
    __tablename__ = 'inventory_snapshots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_product_id: Mapped[int | None] = mapped_column(ForeignKey('canonical_products.id'), index=True)
    source_product_id: Mapped[int | None] = mapped_column(ForeignKey('source_products.id'), index=True)
    source_system_id: Mapped[int] = mapped_column(ForeignKey('source_systems.id'), index=True)
    source_location: Mapped[str | None] = mapped_column(String(255))
    on_hand: Mapped[int | None] = mapped_column(Integer)
    available: Mapped[int | None] = mapped_column(Integer)
    committed: Mapped[int | None] = mapped_column(Integer)
    unavailable: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey('import_batches.id'))


class InventoryReconciliationRun(Base):
    __tablename__ = 'inventory_reconciliation_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text)
    settings_snapshot_json: Mapped[dict | None] = mapped_column(JSON)


class InventoryReconciliationRow(Base):
    __tablename__ = 'inventory_reconciliation_rows'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey('inventory_reconciliation_runs.id'), index=True)
    canonical_product_id: Mapped[int | None] = mapped_column(ForeignKey('canonical_products.id'), index=True)
    shopify_source_product_id: Mapped[int | None] = mapped_column(ForeignKey('source_products.id'))
    fos_source_product_id: Mapped[int | None] = mapped_column(ForeignKey('source_products.id'))
    shopify_handle: Mapped[str | None] = mapped_column(String(255))
    shopify_title: Mapped[str | None] = mapped_column(String(512))
    shopify_sku: Mapped[str | None] = mapped_column(String(128))
    shopify_barcode: Mapped[str | None] = mapped_column(String(128))
    fos_stock_name: Mapped[str | None] = mapped_column(String(512))
    fos_apn: Mapped[str | None] = mapped_column(String(128))
    shopify_current_on_hand: Mapped[int | None] = mapped_column(Integer)
    fos_soh: Mapped[int | None] = mapped_column(Integer)
    proposed_shopify_on_hand: Mapped[int | None] = mapped_column(Integer)
    delta: Mapped[int | None] = mapped_column(Integer)
    sync_status: Mapped[str] = mapped_column(String(64), default='REVIEW')
    warning_flags_json: Mapped[dict | None] = mapped_column(JSON)
    reviewed_by: Mapped[str | None] = mapped_column(String(255))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    review_notes: Mapped[str | None] = mapped_column(Text)


class ManualReviewAction(Base):
    __tablename__ = 'manual_review_actions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(128), index=True)
    action_type: Mapped[str] = mapped_column(String(64))
    old_value_json: Mapped[dict | None] = mapped_column(JSON)
    new_value_json: Mapped[dict | None] = mapped_column(JSON)
    user_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExportRun(Base):
    __tablename__ = 'export_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    export_type: Mapped[str] = mapped_column(String(64), index=True)
    file_path: Mapped[str] = mapped_column(String(512))
    row_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    manifest_json: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)


class AppSetting(Base):
    __tablename__ = 'app_settings'

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
