from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import LinkMethod, LinkStatus
from app.models import CanonicalProduct, SourceProduct, SourceProductLink
from app.services.candidate_service import CandidateService
from app.services.canonical_product_service import CanonicalProductService
from app.services.identifier_service import IdentifierService
from app.services.linking_service import LinkingService

logger = logging.getLogger(__name__)


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
            logger.debug('Skipping locked link for source_product_id=%s', source_product.id)
            return existing_locked

        for identifier_type, value in [
            ('BARCODE', source_product.barcode),
            ('APN', source_product.apn),
            ('PDE', source_product.pde),
            ('SKU', source_product.sku),
        ]:
            hit = self.identifier_service.resolve_exact_identifier(db, identifier_type, value)
            if hit:
                logger.debug('Exact %s match for source_product_id=%s → canonical_product_id=%s', identifier_type, source_product.id, hit.canonical_product_id)
                return self.linking_service.create_or_update_link(
                    db,
                    canonical_product_id=hit.canonical_product_id,
                    source_product_id=source_product.id,
                    link_status=LinkStatus.AUTO_ACCEPTED,
                    link_method=f'EXACT_{identifier_type}',
                    confidence_score=100,
                )

        exact_name = db.scalar(
            select(CanonicalProduct).where(CanonicalProduct.normalized_name == source_product.normalized_title)
        )
        if exact_name:
            logger.debug('Exact name match for source_product_id=%s → canonical_product_id=%s', source_product.id, exact_name.id)
            return self.linking_service.create_or_update_link(
                db,
                canonical_product_id=exact_name.id,
                source_product_id=source_product.id,
                link_status=LinkStatus.AUTO_ACCEPTED,
                link_method=LinkMethod.NORMALIZED_NAME,
                confidence_score=90,
            )

        run_id = str(uuid.uuid4())
        candidates = self.candidate_service.generate_candidates(db, run_id, source_product)
        if candidates:
            top = candidates[0]
            logger.debug('Fuzzy match for source_product_id=%s score=%.1f → NEEDS_REVIEW', source_product.id, top.fuzzy_score or 0)
            return self.linking_service.create_or_update_link(
                db,
                canonical_product_id=top.candidate_canonical_product_id,
                source_product_id=source_product.id,
                link_status=LinkStatus.NEEDS_REVIEW,
                link_method=LinkMethod.FUZZY_PLUS_AI,
                confidence_score=top.fuzzy_score,
                fuzzy_score=top.fuzzy_score,
            )

        canonical = self.canonical_service.create_from_source(db, source_product, 'AUTO')
        logger.debug('No candidates found for source_product_id=%s, created canonical_product_id=%s', source_product.id, canonical.id)
        return self.linking_service.create_or_update_link(
            db,
            canonical_product_id=canonical.id,
            source_product_id=source_product.id,
            link_status=LinkStatus.NEEDS_REVIEW,
            link_method=LinkMethod.CREATED_NEW_CANONICAL,
            confidence_score=40,
        )
