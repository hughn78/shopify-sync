from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import InventoryReconciliationRow, InventoryReconciliationRun, InventorySnapshot, SourceProduct, SourceProductLink, SourceSystem


class ReconciliationService:
    def run(self, db: Session):
        run = InventoryReconciliationRun(
            notes='Generated from canonical-product linked inventory',
            settings_snapshot_json={
                'primary_shopify_location_pattern': settings.primary_shopify_location_pattern,
                'reserve_stock_buffer': settings.reserve_stock_buffer,
            },
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        links = db.scalars(select(SourceProductLink).where(SourceProductLink.link_status.in_(['AUTO_ACCEPTED', 'APPROVED']))).all()
        by_canonical = {}
        for link in links:
            by_canonical.setdefault(link.canonical_product_id, []).append(link)

        for canonical_id, items in by_canonical.items():
            shopify = None
            fos = None
            for link in items:
                source_product = db.get(SourceProduct, link.source_product_id)
                if source_product.handle:
                    shopify = source_product
                if source_product.apn or (source_product.raw_payload_json or {}).get('Stock Name'):
                    fos = source_product
            if not shopify and not fos:
                continue

            shopify_snapshot = db.scalar(
                select(InventorySnapshot).where(InventorySnapshot.source_product_id == (shopify.id if shopify else None)).order_by(InventorySnapshot.id.desc())
            ) if shopify else None
            fos_snapshot = db.scalar(
                select(InventorySnapshot).where(InventorySnapshot.source_product_id == (fos.id if fos else None)).order_by(InventorySnapshot.id.desc())
            ) if fos else None

            shopify_on_hand = shopify_snapshot.on_hand if shopify_snapshot else None
            fos_soh = fos_snapshot.on_hand if fos_snapshot else None
            proposed = max((fos_soh or 0) - settings.reserve_stock_buffer, 0) if fos_soh is not None else shopify_on_hand
            delta = None if proposed is None or shopify_on_hand is None else proposed - shopify_on_hand
            warnings = []
            if shopify and not fos:
                warnings.append('MISSING_FOS_LINK')
            if fos and not shopify:
                warnings.append('MISSING_SHOPIFY_LINK')
            if delta is not None and abs(delta) >= 5:
                warnings.append('LARGE_DELTA')

            row = InventoryReconciliationRow(
                run_id=run.id,
                canonical_product_id=canonical_id,
                shopify_source_product_id=shopify.id if shopify else None,
                fos_source_product_id=fos.id if fos else None,
                shopify_handle=shopify.handle if shopify else None,
                shopify_title=shopify.title if shopify else None,
                shopify_sku=shopify.sku if shopify else None,
                shopify_barcode=shopify.barcode if shopify else None,
                fos_stock_name=fos.title if fos else None,
                fos_apn=fos.apn if fos else None,
                shopify_current_on_hand=shopify_on_hand,
                fos_soh=fos_soh,
                proposed_shopify_on_hand=proposed,
                delta=delta,
                sync_status='READY' if not warnings else 'REVIEW',
                warning_flags_json={'warnings': warnings},
            )
            db.add(row)
        db.commit()
        return run
