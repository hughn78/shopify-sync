from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.enums import ProductReviewStatus
from app.models import CanonicalProduct
from app.services.identifier_service import IdentifierService
from app.utils.normalizers import normalize_name_for_match

logger = logging.getLogger(__name__)


class CanonicalProductService:
    def __init__(self):
        self.identifier_service = IdentifierService()

    def create_from_source(self, db: Session, source_product, source_code: str) -> CanonicalProduct:
        product = CanonicalProduct(
            canonical_name=source_product.title,
            normalized_name=normalize_name_for_match(source_product.title),
            primary_barcode=source_product.barcode,
            primary_apn=source_product.apn,
            primary_pde=source_product.pde,
            review_status=ProductReviewStatus.NEEDS_REVIEW,
            created_from_source=source_code,
            confidence_summary='Created from source import',
        )
        db.add(product)
        db.flush()
        self.identifier_service.attach_identifiers_from_source_product(
            db,
            canonical_product_id=product.id,
            source_product=source_product,
            source=f'CANONICAL_CREATE:{source_code}',
            promote_primary=True,
        )
        db.refresh(product)
        logger.debug('Created canonical product id=%s name=%r source=%s', product.id, product.canonical_name, source_code)
        return product
