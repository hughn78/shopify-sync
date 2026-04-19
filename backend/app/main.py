from __future__ import annotations

from typing import Any, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CandidateLink, CanonicalProduct, SourceProduct, SourceProductLink
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

app = FastAPI(title='Pharmacy Stock Sync')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

import_service = ImportService()
normalization_service = NormalizationService()
source_product_service = SourceProductService()
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
    detected_type, rows = import_service.parse_file(file.filename, content)
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
        detected_type, rows = import_service.parse_file(file.filename, content)
        batch = import_service.create_batch(db, detected_type, file.filename, content, len(rows))

        system = source_product_service.get_source_system(db, detected_type)

        for idx, row in enumerate(rows, start=1):
            normalized = normalization_service.normalize_source_row(row, detected_type)
            if detected_type == 'SHOPIFY_PRODUCTS':
                key = f"{row.get('Handle', '')}:{row.get('Variant SKU', '')}:{idx}"
            elif detected_type == 'SHOPIFY_INVENTORY':
                key = f"{row.get('Handle', '')}:{row.get('SKU', '')}:{row.get('Location', '')}:{idx}"
            elif detected_type == 'FOS':
                key = f"{row.get('APN', '')}:{row.get('PDE', '')}:{idx}"
            elif detected_type == 'PRICEBOOK':
                key = f"{row.get('API PDE', row.get('PDE', ''))}:{row.get('Barcode', '')}:{idx}"
            elif detected_type == 'MASTERCATALOG':
                key = f"{row.get('APN', '')}:{row.get('Name', '')}:{idx}"
            else:
                key = f"{row.get('product_id', row.get('slug', row.get('name', '')))}:{idx}"
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

        results.append({'batch_id': batch.id, 'import_type': detected_type, 'rows': len(rows), 'filename': file.filename})

    return {'imports': results, 'count': len(results)}


@app.get('/api/canonical-products')
def list_canonical_products(db: Session = Depends(get_db)):
    return db.scalars(select(CanonicalProduct).order_by(CanonicalProduct.id.desc())).all()


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
def list_source_products(source: Optional[str] = None, db: Session = Depends(get_db)):
    stmt = select(SourceProduct, SourceSystem.code.label('source_code')).join(SourceSystem, SourceSystem.id == SourceProduct.source_system_id)
    if source:
        stmt = stmt.where(SourceSystem.code == source)
    rows = db.execute(stmt.order_by(SourceProduct.id.desc())).all()
    return [
        {
            **source_product.__dict__,
            'source_code': source_code,
        }
        for source_product, source_code in rows
    ]


@app.get('/api/link-review')
def link_review(db: Session = Depends(get_db)):
    links = db.scalars(select(SourceProductLink).order_by(SourceProductLink.id.desc())).all()
    payload = []
    for link in links:
        source_product = db.get(SourceProduct, link.source_product_id)
        canonical_product = db.get(CanonicalProduct, link.canonical_product_id)
        candidates = db.scalars(
            select(CandidateLink).where(CandidateLink.source_product_id == link.source_product_id).order_by(CandidateLink.candidate_rank.asc())
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
    return payload


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


@app.get('/api/audit-summary')
def audit_summary(db: Session = Depends(get_db)):
    return audit_service.summary(db)


@app.get('/api/import-batches')
def list_import_batches(import_type: Optional[str] = None, db: Session = Depends(get_db)):
    from app.models import ImportBatch
    stmt = select(ImportBatch)
    if import_type:
        stmt = stmt.where(ImportBatch.import_type == import_type)
    return db.scalars(stmt.order_by(ImportBatch.id.desc())).all()


@app.get('/api/settings')
def settings():
    from app.config import settings as app_settings
    return app_settings.model_dump()


def _coerce_int(value: Any) -> Optional[int]:
    if value in (None, ''):
        return None
    try:
        return int(float(value))
    except Exception:
        return None
