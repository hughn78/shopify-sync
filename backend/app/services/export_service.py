from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import EXPORT_DIR
from app.models import ExportRun, InventoryReconciliationRow, SourceProductLink

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ExportService:
    def export_inventory_sync(self, db: Session, run_id: int) -> Path:
        rows = db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run_id)).all()
        payload = [
            {
                'Handle': row.shopify_handle,
                'Title': row.shopify_title,
                'SKU': row.shopify_sku,
                'Barcode': row.shopify_barcode,
                'Current Shopify On Hand': row.shopify_current_on_hand,
                'FOS SOH': row.fos_soh,
                'Proposed Shopify On Hand': row.proposed_shopify_on_hand,
                'Delta': row.delta,
                'Sync Status': row.sync_status,
                'Warnings': ','.join((row.warning_flags_json or {}).get('warnings', [])),
            }
            for row in rows
        ]
        timestamp = _utcnow().strftime('%Y%m%d%H%M%S')
        path = EXPORT_DIR / f'inventory_sync_{run_id}_{timestamp}.csv'
        pd.DataFrame(payload).to_csv(path, index=False)
        db.add(ExportRun(
            export_type='SHOPIFY_INVENTORY_SYNC',
            file_path=str(path),
            row_count=len(payload),
            manifest_json={'run_id': run_id},
        ))
        db.commit()
        logger.info('Exported %d rows for run_id=%s to %s', len(payload), run_id, path)
        return path

    def export_link_report(self, db: Session, status: str, filename_prefix: str) -> Path:
        links = db.scalars(select(SourceProductLink).where(SourceProductLink.link_status == status)).all()
        payload = [
            {
                'link_id': link.id,
                'canonical_product_id': link.canonical_product_id,
                'source_product_id': link.source_product_id,
                'status': link.link_status,
                'method': link.link_method,
                'confidence': link.confidence_score,
                'reason': link.ai_reason,
            }
            for link in links
        ]
        timestamp = _utcnow().strftime('%Y%m%d%H%M%S')
        path = EXPORT_DIR / f'{filename_prefix}_{timestamp}.csv'
        pd.DataFrame(payload).to_csv(path, index=False)
        db.add(ExportRun(
            export_type=filename_prefix.upper(),
            file_path=str(path),
            row_count=len(payload),
            manifest_json={'status': status},
        ))
        db.commit()
        logger.info('Exported link report %s with %d rows to %s', filename_prefix, len(payload), path)
        return path
