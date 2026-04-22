from __future__ import annotations

import logging
import logging.config
from typing import Any, Optional

from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CandidateLink, CanonicalProduct, SourceProduct, SourceProductLink, SourceSystem
from app.routes.dashboard import get_dashboard_summary
from app.schemas import BulkReviewActionRequest, ImportPreviewResponse, ImportPreviewRow, ReviewActionRequest
from app.services.audit_service import AuditService
from app.services.export_service import ExportService
from app.services.import_service import FILE_COLUMN_HINTS, ImportService
from app.services.inventory_service import InventoryService
from app.services.matching_service import MatchingService
from app.services.normalization_service import NormalizationService
from app.services.reconciliation_service import ReconciliationService
from app.services.review_service import ReviewService
from app.services.source_product_service import SourceProductService
from app.services.source_identity_service import SourceIdentityService

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {'format': '%(asctime)s %(levelname)-8s %(name)s %(message)s'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'default'},
    },
    'root': {'level': 'INFO', 'handlers': ['console']},
    'loggers': {
        'app': {'level': 'DEBUG', 'propagate': True},
    },
})

logger = logging.getLogger(__name__)

app = FastAPI(title='Pharmacy Stock Sync')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5174',
    ],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

import_service = ImportService()
normalization_service = NormalizationService()
source_product_service = SourceProductService()
source_identity_service = SourceIdentityService()
matching_service = MatchingService()
inventory_service = InventoryService()
reconciliation_service = ReconciliationService()
review_service = ReviewService()
export_service = ExportService()
audit_service = AuditService()


@app.get('/api/health')
def health():
    return {'ok': True}


@app.get('/api/dashboard')
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard_summary(db)


@app.post('/api/imports/preview', response_model=ImportPreviewResponse)
async def preview_import(file: UploadFile = File(...)):
    content = await file.read()
    try:
        import_service.validate_upload(file.filename or '', content)
        detected_type, rows = import_service.parse_file(file.filename or '', content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    columns = list(rows[0].keys()) if rows else []
    expected = FILE_COLUMN_HINTS.get(detected_type, set())
    return ImportPreviewResponse(
        detected_type=detected_type,
        columns=columns,
        preview_rows=[ImportPreviewRow(row_number=i + 1, data=row) for i, row in enumerate(rows[:10])],
        missing_columns=sorted(list(expected - set(columns))),
        extra_columns=sorted(list(set(columns) - expected)),
    )


@app.post('/api/imports')
async def import_file(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    results = []
    for file in files:
        content = await file.read()
        filename = file.filename or 'unknown'
        try:
            import_service.validate_upload(filename, content)
            detected_type, rows = import_service.parse_file(filename, content)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        batch = import_service.create_batch(db, detected_type, filename, content, len(rows))
        system = source_product_service.get_source_system(db, detected_type)

        row_errors = []
        for idx, row in enumerate(rows, start=1):
            sp = db.begin_nested()
            try:
                normalized = normalization_service.normalize_source_row(row, detected_type)
                key = _build_source_key(detected_type, row, idx)
                source_product = source_product_service.upsert_source_product(db, detected_type, key, {**row, **normalized}, batch.id)

                if detected_type == 'SHOPIFY_INVENTORY':
                    inventory_service.create_snapshot(
                        db,
                        source_product_id=source_product.id,
                        source_system_id=system.id,
                        import_batch_id=batch.id,
                        source_location=normalized.get('location'),
                        on_hand=_coerce_int(row.get('On hand (current)') or row.get('On Hand (current)') or row.get('On hand') or row.get('on_hand')),
                        available=_coerce_int(row.get('Available')),
                        committed=_coerce_int(row.get('Committed')),
                        unavailable=_coerce_int(row.get('Unavailable')),
                    )
                elif detected_type == 'FOS':
                    inventory_service.create_snapshot(
                        db,
                        source_product_id=source_product.id,
                        source_system_id=system.id,
                        import_batch_id=batch.id,
                        source_location='fos',
                        on_hand=_coerce_int(row.get('SOH')),
                    )

                matching_service.resolve_source_product(db, source_product)
                sp.commit()
            except Exception as exc:
                sp.rollback()
                logger.error('Row %d of %r failed: %s', idx, filename, exc)
                row_errors.append({'row': idx, 'error': str(exc)})

        db.commit()
        result = {'batch_id': batch.id, 'import_type': detected_type, 'rows': len(rows), 'filename': filename}
        if row_errors:
            result['row_errors'] = row_errors
        results.append(result)

    return {'imports': results, 'count': len(results)}


@app.get('/api/canonical-products')
def list_canonical_products(
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(CanonicalProduct))
    items = db.scalars(
        select(CanonicalProduct).order_by(CanonicalProduct.id.desc()).limit(limit).offset(offset)
    ).all()
    return {'items': items, 'total': total, 'limit': limit, 'offset': offset}


@app.get('/api/review-options')
def review_options(db: Session = Depends(get_db)):
    canonicals = db.scalars(select(CanonicalProduct).order_by(CanonicalProduct.canonical_name.asc())).all()
    return [
        {
            'id': canonical.id,
            'canonical_name': canonical.canonical_name,
            'primary_barcode': canonical.primary_barcode,
            'primary_apn': canonical.primary_apn,
            'primary_pde': canonical.primary_pde,
            'review_status': canonical.review_status,
        }
        for canonical in canonicals
    ]


@app.get('/api/source-products')
def list_source_products(
    source: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(SourceProduct, SourceSystem.code.label('source_code')).join(SourceSystem, SourceSystem.id == SourceProduct.source_system_id)
    if source:
        stmt = stmt.where(SourceSystem.code == source)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.order_by(SourceProduct.id.desc()).limit(limit).offset(offset)).all()
    return {
        'items': [
            {**source_product.__dict__, 'source_code': source_code}
            for source_product, source_code in rows
        ],
        'total': total,
        'limit': limit,
        'offset': offset,
    }


@app.get('/api/link-review')
def link_review(
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(SourceProductLink))
    links = db.scalars(
        select(SourceProductLink).order_by(SourceProductLink.id.desc()).limit(limit).offset(offset)
    ).all()
    payload = []
    for link in links:
        source_product = db.get(SourceProduct, link.source_product_id)
        canonical_product = db.get(CanonicalProduct, link.canonical_product_id)
        candidates = db.scalars(
            select(CandidateLink)
            .where(CandidateLink.source_product_id == link.source_product_id)
            .order_by(CandidateLink.candidate_rank.asc())
        ).all()
        payload.append({
            'id': link.id,
            'link_status': link.link_status,
            'link_method': link.link_method,
            'confidence_score': link.confidence_score,
            'fuzzy_score': link.fuzzy_score,
            'ai_score': link.ai_score,
            'ai_reason': link.ai_reason,
            'locked': link.locked,
            'excluded': link.excluded,
            'review_notes': link.review_notes,
            'source_product': source_product,
            'canonical_product': canonical_product,
            'candidates': [
                {
                    'id': candidate.id,
                    'candidate_canonical_product_id': candidate.candidate_canonical_product_id,
                    'candidate_rank': candidate.candidate_rank,
                    'match_method': candidate.match_method,
                    'fuzzy_score': candidate.fuzzy_score,
                    'ai_score': candidate.ai_score,
                    'ai_reason': candidate.ai_reason,
                    'proposed_action': candidate.proposed_action,
                    'canonical_product': db.get(CanonicalProduct, candidate.candidate_canonical_product_id) if candidate.candidate_canonical_product_id else None,
                }
                for candidate in candidates
            ],
        })
    return {'items': payload, 'total': total, 'limit': limit, 'offset': offset}


@app.post('/api/link-review/bulk')
def apply_bulk_review_action(request: BulkReviewActionRequest, db: Session = Depends(get_db)):
    links = db.scalars(select(SourceProductLink).where(SourceProductLink.id.in_(request.link_ids))).all()
    if not links:
        raise HTTPException(status_code=404, detail='No matching links found')
    updated_links = review_service.apply_bulk_action(
        db,
        links,
        request.action,
        request.note,
        request.canonical_product_id,
        request.locked,
    )
    return {
        'count': len(updated_links),
        'ids': [link.id for link in updated_links],
        'action': request.action,
    }


@app.post('/api/link-review/{link_id}')
def apply_review_action(link_id: int, request: ReviewActionRequest, db: Session = Depends(get_db)):
    link = db.get(SourceProductLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail='Link not found')
    updated = review_service.apply_action(db, link, request.action, request.note, request.canonical_product_id, request.locked)
    return {'id': updated.id, 'status': updated.link_status}


@app.post('/api/reconciliation-runs')
def create_reconciliation_run(db: Session = Depends(get_db)):
    run = reconciliation_service.run(db)
    return {'run_id': run.id}


@app.get('/api/reconciliation-rows/{run_id}')
def list_reconciliation_rows(run_id: int, db: Session = Depends(get_db)):
    from app.models import InventoryReconciliationRow
    return db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run_id)).all()


@app.post('/api/exports/inventory/{run_id}')
def export_inventory(run_id: int, db: Session = Depends(get_db)):
    path = export_service.export_inventory_sync(db, run_id)
    return {'file_path': str(path)}


@app.post('/api/exports/shopify-upload/{run_id}')
def export_shopify_upload_bundle(run_id: int, db: Session = Depends(get_db)):
    return export_service.export_shopify_upload_bundle(db, run_id)


@app.get('/api/exports/shopify-upload/{run_id}/summary')
def shopify_upload_bundle_summary(run_id: int, db: Session = Depends(get_db)):
    return export_service.summarize_shopify_upload_bundle(db, run_id)


@app.post('/api/exports/shopify-products')
def export_shopify_products_bundle(db: Session = Depends(get_db)):
    return export_service.export_shopify_products_bundle(db)


@app.get('/api/audit-summary')
def audit_summary(db: Session = Depends(get_db)):
    return audit_service.summary(db)


@app.get('/api/source-identity/backfill-preview')
def source_identity_backfill_preview(db: Session = Depends(get_db)):
    return source_identity_service.preview_backfill(db)


@app.post('/api/source-identity/backfill-apply')
def source_identity_backfill_apply(db: Session = Depends(get_db)):
    return source_identity_service.apply_backfill(db)


@app.post('/api/identifiers/backfill')
def identifiers_backfill(db: Session = Depends(get_db)):
    from app.services.identifier_service import IdentifierService
    return IdentifierService().backfill_identifiers_from_links(db)


@app.get('/api/import-batches')
def list_import_batches(
    import_type: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    from app.models import ImportBatch
    stmt = select(ImportBatch)
    if import_type:
        stmt = stmt.where(ImportBatch.import_type == import_type)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(ImportBatch.id.desc()).limit(limit).offset(offset)).all()
    return {'items': items, 'total': total, 'limit': limit, 'offset': offset}


@app.get('/api/settings')
def settings():
    from app.config import settings as app_settings
    return app_settings.model_dump()


_STATIC_DIR = Path(__file__).parent / 'static'

if _STATIC_DIR.exists():
    app.mount('/assets', StaticFiles(directory=_STATIC_DIR / 'assets'), name='assets')

    @app.get('/{full_path:path}', include_in_schema=False)
    def spa_fallback(full_path: str):
        return FileResponse(_STATIC_DIR / 'index.html')
else:
    logger.warning('No built frontend found at %s — run `cd frontend && npm run build` first', _STATIC_DIR)


def _build_source_key(detected_type: str, row: dict, idx: int) -> str:
    if detected_type == 'SHOPIFY_PRODUCTS':
        variant_id = _pick_value(row, 'Variant ID', 'variant_id', 'Variant Id')
        if variant_id:
            return f"shopify-product-variant:{variant_id}"
        sku = _pick_value(row, 'Variant SKU', 'SKU', 'sku')
        handle = _pick_value(row, 'Handle', 'handle')
        if handle or sku:
            return f"shopify-product:{handle or ''}:{sku or ''}"
        product_id = _pick_value(row, 'Product ID', 'product_id', 'Product Id')
        if product_id:
            return f"shopify-product-id:{product_id}"
        return f"shopify-product-row:{idx}"
    if detected_type == 'SHOPIFY_INVENTORY':
        inventory_item_id = _pick_value(row, 'Inventory Item ID', 'inventory_item_id', 'Inventory Item Id')
        location_id = _pick_value(row, 'Location ID', 'location_id', 'Location Id')
        if inventory_item_id and location_id:
            return f"shopify-inventory:{inventory_item_id}:{location_id}"
        sku = _pick_value(row, 'SKU', 'sku')
        location = _pick_value(row, 'Location', 'location')
        if sku or location:
            return f"shopify-inventory-sku:{sku or ''}:{location or ''}"
        handle = _pick_value(row, 'Handle', 'handle')
        if handle:
            return f"shopify-inventory-handle:{handle}"
        return f"shopify-inventory-row:{idx}"
    if detected_type == 'FOS':
        apn = _pick_value(row, 'APN', 'apn')
        pde = _pick_value(row, 'PDE', 'pde', 'API PDE')
        barcode = _pick_value(row, 'Barcode', 'barcode')
        if apn:
            return f"fos-apn:{apn}"
        if pde:
            return f"fos-pde:{pde}"
        if barcode:
            return f"fos-barcode:{barcode}"
        return f"fos-row:{idx}"
    if detected_type == 'PRICEBOOK':
        return f"{row.get('API PDE', row.get('PDE', ''))}:{row.get('Barcode', '')}:{idx}"
    if detected_type == 'MASTERCATALOG':
        return f"{row.get('APN', '')}:{row.get('Name', '')}:{idx}"
    return f"{row.get('product_id', row.get('slug', row.get('name', '')))}:{idx}"


def _pick_value(row: dict, *keys: str) -> Optional[str]:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _coerce_int(value: Any) -> Optional[int]:
    if value in (None, ''):
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError) as exc:
        logger.debug('Could not coerce %r to int: %s', value, exc)
        return None
