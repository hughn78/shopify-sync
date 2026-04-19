from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import CanonicalProduct
from app.utils.normalizers import normalize_name_for_match


class CanonicalProductService:
    def create_from_source(self, db: Session, source_product, source_code: str) -> CanonicalProduct:
        product = CanonicalProduct(
            canonical_name=source_product.title,
            normalized_name=normalize_name_for_match(source_product.title),
            primary_barcode=source_product.barcode,
            primary_apn=source_product.apn,
            primary_pde=source_product.pde,
            review_status='NEEDS_REVIEW',
            created_from_source=source_code,
            confidence_summary='Created from source import',
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
