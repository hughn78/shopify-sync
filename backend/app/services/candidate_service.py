from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CandidateLink, CanonicalProduct


class CandidateService:
    def generate_candidates(self, db: Session, run_id: str, source_product, limit: int = 5):
        canonicals = db.scalars(select(CanonicalProduct)).all()
        scored = []
        for canonical in canonicals:
            if not canonical.normalized_name or not source_product.normalized_title:
                continue
            score = fuzz.token_sort_ratio(source_product.normalized_title, canonical.normalized_name)
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
                proposed_action='REVIEW' if score < 85 else 'AUTO_ACCEPT',
            )
            db.add(candidate)
            created.append(candidate)
        db.commit()
        return created
