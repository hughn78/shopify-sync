from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CanonicalProduct, SourceProduct, SourceProductLink
from app.services.candidate_service import CandidateService
from app.services.canonical_product_service import CanonicalProductService
from app.services.identifier_service import IdentifierService
from app.services.linking_service import LinkingService


class MatchingService:
    def __init__(self):
        self.identifier_service = IdentifierService()
        self.candidate_service = CandidateService()
        self.canonical_service = CanonicalProductService()
        self.linking_service = LinkingService()

    def resolve_source_product(self, db: Session, source_product: SourceProduct):
        existing_locked = db.scalar(
            select(SourceProductLink).where(
                SourceProductLink.source_product_id == source_product.id,
                SourceProductLink.locked.is_(True),
            )
        )
        if existing_locked:
            return existing_locked

        for identifier_type, value in [
            ('BARCODE', source_product.barcode),
            ('APN', source_product.apn),
            ('PDE', source_product.pde),
            ('SKU', source_product.sku),
        ]:
            hit = self.identifier_service.resolve_exact_identifier(db, identifier_type, value)
            if hit:
                return self.linking_service.create_or_update_link(
                    db,
                    canonical_product_id=hit.canonical_product_id,
                    source_product_id=source_product.id,
                    link_status='AUTO_ACCEPTED',
                    link_method=f'EXACT_{identifier_type}',
                    confidence_score=100,
                )

        exact_name = db.scalar(
            select(CanonicalProduct).where(CanonicalProduct.normalized_name == source_product.normalized_title)
        )
        if exact_name:
            return self.linking_service.create_or_update_link(
                db,
                canonical_product_id=exact_name.id,
                source_product_id=source_product.id,
                link_status='AUTO_ACCEPTED',
                link_method='NORMALIZED_NAME',
                confidence_score=90,
            )

        run_id = str(uuid.uuid4())
        candidates = self.candidate_service.generate_candidates(db, run_id, source_product)
        if candidates:
            top = candidates[0]
            status = 'AUTO_ACCEPTED' if (top.fuzzy_score or 0) >= 90 else 'NEEDS_REVIEW'
            return self.linking_service.create_or_update_link(
                db,
                canonical_product_id=top.candidate_canonical_product_id,
                source_product_id=source_product.id,
                link_status=status,
                link_method='FUZZY_PLUS_AI',
                confidence_score=top.fuzzy_score,
                fuzzy_score=top.fuzzy_score,
                ai_reason='AI optional layer not enabled',
            )

        canonical = self.canonical_service.create_from_source(db, source_product, 'AUTO')
        return self.linking_service.create_or_update_link(
            db,
            canonical_product_id=canonical.id,
            source_product_id=source_product.id,
            link_status='NEEDS_REVIEW',
            link_method='CREATED_NEW_CANONICAL',
            confidence_score=40,
        )
