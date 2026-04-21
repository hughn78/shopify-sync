from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import EXPORT_DIR
from app.models import ExportRun, InventoryReconciliationRow, SourceProductLink

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ExportService:
    SAFE_UPLOAD_COLUMNS = [
        'Handle',
        'Title',
        'Variant ID',
        'Inventory Item ID',
        'Location ID',
        'Location Name',
        'SKU',
        'Barcode',
        'Current Shopify On Hand',
        'New Shopify On Hand',
        'Delta',
    ]

    EXCEPTION_COLUMNS = SAFE_UPLOAD_COLUMNS + [
        'FOS SOH',
        'Sync Status',
        'Blockers',
    ]

    def _row_warnings(self, row: InventoryReconciliationRow) -> list[str]:
        return list((row.warning_flags_json or {}).get('warnings', []))

    def _safe_upload_blockers(self, row: InventoryReconciliationRow) -> list[str]:
        blockers: list[str] = []
        warnings = set(self._row_warnings(row))
        if row.sync_status != 'READY':
            blockers.append('SYNC_STATUS_NOT_READY')
        if not row.shopify_inventory_item_id:
            blockers.append('MISSING_SHOPIFY_INVENTORY_ITEM_ID')
        if not row.shopify_location_id:
            blockers.append('MISSING_SHOPIFY_LOCATION_ID')
        if row.proposed_shopify_on_hand is None:
            blockers.append('MISSING_PROPOSED_QUANTITY')
        if row.shopify_source_product_id is None:
            blockers.append('MISSING_SHOPIFY_LINK')
        if row.fos_source_product_id is None:
            blockers.append('MISSING_FOS_LINK')
        if warnings:
            blockers.extend(sorted(warnings))
        return blockers

    def _audit_payload_row(self, row: InventoryReconciliationRow) -> dict[str, Any]:
        return {
            'Handle': row.shopify_handle,
            'Title': row.shopify_title,
            'Variant ID': row.shopify_variant_id,
            'Inventory Item ID': row.shopify_inventory_item_id,
            'Location ID': row.shopify_location_id,
            'Location Name': row.shopify_location_name,
            'SKU': row.shopify_sku,
            'Barcode': row.shopify_barcode,
            'Current Shopify On Hand': row.shopify_current_on_hand,
            'FOS SOH': row.fos_soh,
            'Proposed Shopify On Hand': row.proposed_shopify_on_hand,
            'Delta': row.delta,
            'Sync Status': row.sync_status,
            'Warnings': ','.join(self._row_warnings(row)),
        }

    def export_inventory_sync(self, db: Session, run_id: int) -> Path:
        rows = db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run_id)).all()
        payload = [self._audit_payload_row(row) for row in rows]
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

    def export_shopify_upload_bundle(self, db: Session, run_id: int) -> dict[str, Any]:
        rows = db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run_id)).all()

        safe_rows = []
        exception_rows = []
        for row in rows:
            blockers = self._safe_upload_blockers(row)
            upload_row = {
                'Handle': row.shopify_handle,
                'Title': row.shopify_title,
                'Variant ID': row.shopify_variant_id,
                'Inventory Item ID': row.shopify_inventory_item_id,
                'Location ID': row.shopify_location_id,
                'Location Name': row.shopify_location_name,
                'SKU': row.shopify_sku,
                'Barcode': row.shopify_barcode,
                'Current Shopify On Hand': row.shopify_current_on_hand,
                'New Shopify On Hand': row.proposed_shopify_on_hand,
                'Delta': row.delta,
            }
            if blockers:
                exception_rows.append({
                    **upload_row,
                    'FOS SOH': row.fos_soh,
                    'Sync Status': row.sync_status,
                    'Blockers': ','.join(blockers),
                })
            else:
                safe_rows.append(upload_row)

        timestamp = _utcnow().strftime('%Y%m%d%H%M%S')
        safe_path = EXPORT_DIR / f'safe_upload_to_shopify_{run_id}_{timestamp}.csv'
        exceptions_path = EXPORT_DIR / f'exceptions_needing_review_{run_id}_{timestamp}.csv'

        pd.DataFrame(safe_rows, columns=self.SAFE_UPLOAD_COLUMNS).to_csv(safe_path, index=False)
        pd.DataFrame(exception_rows, columns=self.EXCEPTION_COLUMNS).to_csv(exceptions_path, index=False)

        db.add_all([
            ExportRun(
                export_type='SHOPIFY_SAFE_UPLOAD',
                file_path=str(safe_path),
                row_count=len(safe_rows),
                manifest_json={'run_id': run_id, 'kind': 'safe_upload'},
            ),
            ExportRun(
                export_type='SHOPIFY_UPLOAD_EXCEPTIONS',
                file_path=str(exceptions_path),
                row_count=len(exception_rows),
                manifest_json={'run_id': run_id, 'kind': 'exceptions'},
            ),
        ])
        db.commit()

        logger.info('Exported Shopify upload bundle for run_id=%s: safe=%d exceptions=%d', run_id, len(safe_rows), len(exception_rows))
        return {
            'safe_upload_path': str(safe_path),
            'exceptions_path': str(exceptions_path),
            'safe_count': len(safe_rows),
            'exception_count': len(exception_rows),
            'blocker_summary': self.summarize_shopify_upload_bundle(db, run_id),
        }

    def summarize_shopify_upload_bundle(self, db: Session, run_id: int) -> dict[str, Any]:
        rows = db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run_id)).all()
        blocker_counts: dict[str, int] = {}
        safe_ids: list[int] = []
        exception_ids: list[int] = []

        for row in rows:
            blockers = self._safe_upload_blockers(row)
            if blockers:
                exception_ids.append(row.id)
                for blocker in blockers:
                    blocker_counts[blocker] = blocker_counts.get(blocker, 0) + 1
            else:
                safe_ids.append(row.id)

        return {
            'run_id': run_id,
            'total_rows': len(rows),
            'safe_count': len(safe_ids),
            'exception_count': len(exception_ids),
            'safe_row_ids': safe_ids,
            'exception_row_ids': exception_ids,
            'blocker_counts': blocker_counts,
        }

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
