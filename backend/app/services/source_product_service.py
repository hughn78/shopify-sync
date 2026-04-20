from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SourceProduct, SourceSystem

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SourceProductService:
    def get_source_system(self, db: Session, code: str) -> SourceSystem:
        system = db.scalar(select(SourceSystem).where(SourceSystem.code == code))
        if system:
            return system
        system = SourceSystem(code=code, name=code.replace('_', ' ').title())
        db.add(system)
        db.commit()
        db.refresh(system)
        logger.info('Created source system code=%s', code)
        return system

    def upsert_source_product(self, db: Session, source_code: str, source_record_key: str, data: dict, batch_id: int) -> SourceProduct:
        system = self.get_source_system(db, source_code)
        product = db.scalar(
            select(SourceProduct).where(
                SourceProduct.source_system_id == system.id,
                SourceProduct.source_record_key == source_record_key,
            )
        )
        now = _utcnow()
        payload = {
            'external_product_id': data.get('external_product_id') or data.get('Handle') or data.get('handle') or data.get('product_id') or data.get('slug') or source_record_key,
            'external_variant_id': data.get('external_variant_id'),
            'external_inventory_item_id': data.get('external_inventory_item_id'),
            'external_location_id': data.get('external_location_id'),
            'source_location_name': data.get('source_location_name') or data.get('Location') or data.get('location'),
            'handle': data.get('Handle') or data.get('handle') or data.get('slug') or data.get('url'),
            'title': data.get('Title') or data.get('title') or data.get('name') or data.get('Name') or data.get('Product') or data.get('Description') or data.get('Stock Name') or data.get('Full Name') or 'Untitled',
            'normalized_title': data.get('normalized_title'),
            'sku': data.get('sku'),
            'barcode': data.get('barcode'),
            'apn': data.get('apn'),
            'pde': data.get('pde'),
            'vendor': data.get('Vendor') or data.get('vendor') or data.get('brand') or data.get('Brand') or data.get('Generic'),
            'product_type': data.get('Type') or data.get('Product Type') or data.get('Dept') or data.get('product_type') or data.get('category') or data.get('subcategory'),
            'status': data.get('Status') or data.get('status') or data.get('availability'),
            'raw_payload_json': data,
            'last_import_batch_id': batch_id,
            'last_seen_at': now,
            'is_active': True,
        }
        if product:
            for key, value in payload.items():
                setattr(product, key, value)
            logger.debug('Updated source product id=%s key=%s', product.id, source_record_key)
        else:
            product = SourceProduct(
                source_system_id=system.id,
                source_record_key=source_record_key,
                first_seen_at=now,
                **payload,
            )
            db.add(product)
            logger.debug('Created source product key=%s system=%s', source_record_key, source_code)
        db.flush()
        db.refresh(product)
        return product
