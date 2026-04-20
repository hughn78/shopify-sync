from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InventorySnapshot, SourceProduct, SourceProductLink, SourceSystem


def _text(value: object | None) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def stable_source_key_for_product(source_code: str, product: SourceProduct) -> str:
    if source_code == 'SHOPIFY_PRODUCTS':
        if product.external_variant_id:
            return f'shopify-product-variant:{product.external_variant_id}'
        if product.handle or product.sku:
            return f'shopify-product:{product.handle or ""}:{product.sku or ""}'
        if product.external_product_id:
            return f'shopify-product-id:{product.external_product_id}'
        return f'legacy-source:{product.id}'

    if source_code == 'SHOPIFY_INVENTORY':
        if product.external_inventory_item_id and product.external_location_id:
            return f'shopify-inventory:{product.external_inventory_item_id}:{product.external_location_id}'
        if product.sku or product.source_location_name:
            return f'shopify-inventory-sku:{product.sku or ""}:{product.source_location_name or ""}'
        if product.handle:
            return f'shopify-inventory-handle:{product.handle}'
        return f'legacy-source:{product.id}'

    if source_code == 'FOS':
        if product.apn:
            return f'fos-apn:{product.apn}'
        if product.pde:
            return f'fos-pde:{product.pde}'
        if product.barcode:
            return f'fos-barcode:{product.barcode}'
        return f'legacy-source:{product.id}'

    base = _text(product.external_product_id) or _text(product.handle) or _text(product.title)
    return f'{source_code.lower()}:{base or product.id}'


@dataclass
class LegacyDuplicateGroup:
    source_code: str
    stable_key: str
    survivor_id: int
    duplicate_ids: list[int]


class SourceIdentityService:
    def build_duplicate_groups(self, db: Session) -> list[LegacyDuplicateGroup]:
        system_codes = dict(db.execute(select(SourceSystem.id, SourceSystem.code)).all())
        products = db.scalars(select(SourceProduct).order_by(SourceProduct.id.asc())).all()

        grouped: dict[tuple[int, str], list[SourceProduct]] = {}
        for product in products:
            source_code = system_codes.get(product.source_system_id)
            if not source_code:
                continue
            stable_key = stable_source_key_for_product(source_code, product)
            grouped.setdefault((product.source_system_id, stable_key), []).append(product)

        duplicates: list[LegacyDuplicateGroup] = []
        for (source_system_id, stable_key), items in grouped.items():
            if len(items) < 2:
                continue
            survivor = self._choose_survivor(db, items)
            duplicate_ids = [item.id for item in items if item.id != survivor.id]
            if not duplicate_ids:
                continue
            duplicates.append(LegacyDuplicateGroup(
                source_code=system_codes[source_system_id],
                stable_key=stable_key,
                survivor_id=survivor.id,
                duplicate_ids=duplicate_ids,
            ))
        return duplicates

    def preview_backfill(self, db: Session) -> dict:
        groups = self.build_duplicate_groups(db)
        return {
            'groups': [
                {
                    'source_code': group.source_code,
                    'stable_key': group.stable_key,
                    'survivor_id': group.survivor_id,
                    'duplicate_ids': group.duplicate_ids,
                    'duplicate_count': len(group.duplicate_ids),
                }
                for group in groups
            ],
            'group_count': len(groups),
            'duplicate_count': sum(len(group.duplicate_ids) for group in groups),
        }

    def apply_backfill(self, db: Session) -> dict:
        groups = self.build_duplicate_groups(db)
        for group in groups:
            for duplicate_id in group.duplicate_ids:
                db.query(SourceProductLink).filter(SourceProductLink.source_product_id == duplicate_id).update({'source_product_id': group.survivor_id})
                db.query(InventorySnapshot).filter(InventorySnapshot.source_product_id == duplicate_id).update({'source_product_id': group.survivor_id})
                duplicate = db.get(SourceProduct, duplicate_id)
                if duplicate:
                    duplicate.is_active = False
                    duplicate.status = 'MERGED_DUPLICATE'
        db.commit()
        return self.preview_backfill(db)

    def _choose_survivor(self, db: Session, items: list[SourceProduct]) -> SourceProduct:
        def score(product: SourceProduct) -> tuple[int, int, int, int]:
            link_count = db.query(SourceProductLink).filter(SourceProductLink.source_product_id == product.id).count()
            snapshot_count = db.query(InventorySnapshot).filter(InventorySnapshot.source_product_id == product.id).count()
            identifier_score = sum(1 for value in [product.external_variant_id, product.external_inventory_item_id, product.external_location_id, product.apn, product.pde, product.barcode, product.sku] if value)
            return (link_count, snapshot_count, identifier_score, -product.id)

        return max(items, key=score)
