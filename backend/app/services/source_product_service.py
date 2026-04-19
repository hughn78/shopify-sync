from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SourceProduct, SourceSystem


class SourceProductService:
    def get_source_system(self, db: Session, code: str) -> SourceSystem:
        system = db.scalar(select(SourceSystem).where(SourceSystem.code == code))
        if system:
            return system
        system = SourceSystem(code=code, name=code.replace('_', ' ').title())
        db.add(system)
        db.commit()
        db.refresh(system)
        return system

    def upsert_source_product(self, db: Session, source_code: str, source_record_key: str, data: dict, batch_id: int) -> SourceProduct:
        system = self.get_source_system(db, source_code)
        product = db.scalar(
            select(SourceProduct).where(
                SourceProduct.source_system_id == system.id,
                SourceProduct.source_record_key == source_record_key,
            )
        )
        now = datetime.utcnow()
        payload = {
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
        else:
            product = SourceProduct(
                source_system_id=system.id,
                source_record_key=source_record_key,
                external_product_id=data.get('Handle') or data.get('handle') or data.get('product_id') or data.get('slug') or source_record_key,
                first_seen_at=now,
                **payload,
            )
            db.add(product)
        db.commit()
        db.refresh(product)
        return product
