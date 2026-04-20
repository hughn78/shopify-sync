from __future__ import annotations

import logging

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import CandidateAction
from app.models import CandidateLink, CanonicalProduct

logger = logging.getLogger(__name__)


class CandidateService:
    def generate_candidates(self, db: Session, run_id: str, source_product, limit: int = 5):
        if not source_product.normalized_title:
            return []

        source_tokens = set(source_product.normalized_title.split())

        # Load only canonicals that have a normalized name, then pre-filter by token overlap
        # before running the expensive fuzzy score — reduces O(n) work significantly.
        canonicals = db.scalars(
            select(CanonicalProduct).where(CanonicalProduct.normalized_name.isnot(None))
        ).all()

        scored = []
        for canonical in canonicals:
            canon_tokens = set(canonical.normalized_name.split())
            if not source_tokens & canon_tokens:
                continue
            score = fuzz.token_sort_ratio(source_product.normalized_title, canonical.normalized_name)
            if score >= settings.review_threshold:
                scored.append((canonical, score))

        scored.sort(key=lambda item: item[1], reverse=True)

        created = []
        for rank, (canonical, score) in enumerate(scored[:limit], start=1):
            candidate = CandidateLink(
                run_id=run_id,
                source_product_id=source_product.id,
                candidate_canonical_product_id=canonical.id,
                candidate_rank=rank,
                match_method='FUZZY',
                fuzzy_score=score,
                proposed_action=CandidateAction.REVIEW if score < settings.auto_accept_threshold else CandidateAction.AUTO_ACCEPT,
            )
            db.add(candidate)
            created.append(candidate)

        db.flush()
        logger.debug('Generated %d candidates for source_product_id=%s (run=%s)', len(created), source_product.id, run_id)
        return created
