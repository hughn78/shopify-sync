from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import EXPORT_DIR
from app.models import ExportRun, InventoryReconciliationRow, SourceProduct, SourceProductLink

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ExportService:
    SAFE_UPLOAD_COLUMNS = [
        'Handle',
        'Title',
        'Option1 Name',
        'Option1 Value',
        'Option2 Name',
        'Option2 Value',
        'Option3 Name',
        'Option3 Value',
        'SKU',
        'HS Code',
        'COO',
        'Location',
        'Bin name',
        'Incoming (not editable)',
        'Unavailable (not editable)',
        'Committed (not editable)',
        'Available (not editable)',
        'On hand (current)',
        'On hand (new)',
        'Variant ID',
        'Inventory Item ID',
        'Location ID',
        'Barcode',
        'Delta',
    ]

    EXCEPTION_COLUMNS = SAFE_UPLOAD_COLUMNS + [
        'FOS SOH',
        'Sync Status',
        'Blockers',
    ]

    PRODUCT_EXPORT_COLUMNS = [
        'Handle',
        'Title',
        'Body (HTML)',
        'Vendor',
        'Product Category',
        'Type',
        'Tags',
        'Published',
        'Option1 Name',
        'Option1 Value',
        'Option2 Name',
        'Option2 Value',
        'Option3 Name',
        'Option3 Value',
        'Variant SKU',
        'Variant Barcode',
        'Variant Price',
        'Cost per item',
        'Image Src',
        'Status',
    ]

    def _coalesce_payload_value(self, payload: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in payload and payload[key] not in (None, ''):
                return payload[key]
        return None

    def project_shopify_product_row(self, source_product: SourceProduct) -> dict[str, Any]:
        payload = source_product.raw_payload_json or {}
        return {
            'Handle': self._coalesce_payload_value(payload, 'Handle', 'handle') or source_product.handle,
            'Title': self._coalesce_payload_value(payload, 'Title', 'title') or source_product.title,
            'Body (HTML)': self._coalesce_payload_value(payload, 'Body (HTML)', 'Body HTML', 'body_html'),
            'Vendor': self._coalesce_payload_value(payload, 'Vendor', 'vendor') or source_product.vendor,
            'Product Category': self._coalesce_payload_value(payload, 'Product Category', 'Google Shopping / Google Product Category'),
            'Type': self._coalesce_payload_value(payload, 'Type', 'Product Type', 'product_type') or source_product.product_type,
            'Tags': self._coalesce_payload_value(payload, 'Tags', 'tags'),
            'Published': self._coalesce_payload_value(payload, 'Published', 'published'),
            'Option1 Name': self._coalesce_payload_value(payload, 'Option1 Name') or 'Title',
            'Option1 Value': self._coalesce_payload_value(payload, 'Option1 Value') or 'Default Title',
            'Option2 Name': self._coalesce_payload_value(payload, 'Option2 Name'),
            'Option2 Value': self._coalesce_payload_value(payload, 'Option2 Value'),
            'Option3 Name': self._coalesce_payload_value(payload, 'Option3 Name'),
            'Option3 Value': self._coalesce_payload_value(payload, 'Option3 Value'),
            'Variant SKU': self._coalesce_payload_value(payload, 'Variant SKU', 'SKU') or source_product.sku,
            'Variant Barcode': self._coalesce_payload_value(payload, 'Variant Barcode', 'Barcode') or source_product.barcode,
            'Variant Price': self._coalesce_payload_value(payload, 'Variant Price', 'Price'),
            'Cost per item': self._coalesce_payload_value(payload, 'Cost per item', 'Cost'),
            'Image Src': self._coalesce_payload_value(payload, 'Image Src', 'Image URL', 'image_src'),
            'Status': self._coalesce_payload_value(payload, 'Status', 'status') or source_product.status,
        }

    def _shopify_product_export_blockers(self, row: dict[str, Any]) -> list[str]:
        blockers: list[str] = []
        if not row.get('Handle'):
            blockers.append('MISSING_HANDLE')
        if not row.get('Title'):
            blockers.append('MISSING_TITLE')
        if not row.get('Variant SKU'):
            blockers.append('MISSING_VARIANT_SKU')
        if not row.get('Status'):
            blockers.append('MISSING_STATUS')
        return blockers

    def export_shopify_products_bundle(self, db: Session) -> dict[str, Any]:
        rows = db.scalars(
            select(SourceProduct).join(SourceProductLink, SourceProductLink.source_product_id == SourceProduct.id).where(SourceProduct.external_variant_id.is_not(None))
        ).all()

        safe_rows = []
        exception_rows = []

        for source_product in rows:
            projected = self.project_shopify_product_row(source_product)
            blockers = self._shopify_product_export_blockers(projected)
            if blockers:
                exception_rows.append({**projected, 'Blockers': ','.join(blockers)})
            else:
                safe_rows.append(projected)

        timestamp = _utcnow().strftime('%Y%m%d%H%M%S')
        safe_path = EXPORT_DIR / f'shopify_products_safe_{timestamp}.csv'
        exceptions_path = EXPORT_DIR / f'shopify_products_exceptions_{timestamp}.csv'

        pd.DataFrame(safe_rows, columns=self.PRODUCT_EXPORT_COLUMNS).to_csv(safe_path, index=False)
        pd.DataFrame(exception_rows, columns=[*self.PRODUCT_EXPORT_COLUMNS, 'Blockers']).to_csv(exceptions_path, index=False)

        db.add_all([
            ExportRun(
                export_type='SHOPIFY_PRODUCTS_SAFE',
                file_path=str(safe_path),
                row_count=len(safe_rows),
                manifest_json={'kind': 'safe_products'},
            ),
            ExportRun(
                export_type='SHOPIFY_PRODUCTS_EXCEPTIONS',
                file_path=str(exceptions_path),
                row_count=len(exception_rows),
                manifest_json={'kind': 'product_exceptions'},
            ),
        ])
        db.commit()

        return {
            'safe_products_path': str(safe_path),
            'exceptions_path': str(exceptions_path),
            'safe_count': len(safe_rows),
            'exception_count': len(exception_rows),
        }

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
                'Option1 Name': 'Title',
                'Option1 Value': 'Default Title',
                'Option2 Name': None,
                'Option2 Value': None,
                'Option3 Name': None,
                'Option3 Value': None,
                'SKU': row.shopify_sku,
                'HS Code': None,
                'COO': None,
                'Location': row.shopify_location_name,
                'Bin name': None,
                'Incoming (not editable)': 0,
                'Unavailable (not editable)': 0,
                'Committed (not editable)': 0,
                'Available (not editable)': row.shopify_current_on_hand,
                'On hand (current)': row.shopify_current_on_hand,
                'On hand (new)': row.proposed_shopify_on_hand,
                'Variant ID': row.shopify_variant_id,
                'Inventory Item ID': row.shopify_inventory_item_id,
                'Location ID': row.shopify_location_id,
                'Barcode': row.shopify_barcode,
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
