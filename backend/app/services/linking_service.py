from __future__ import annotations
from typing import Optional

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SourceProductLink


class LinkingService:
    def create_or_update_link(
        self,
        db: Session,
        canonical_product_id: int,
        source_product_id: int,
        link_status: str,
        link_method: str,
        confidence_score: Optional[float] = None,
        fuzzy_score: Optional[float] = None,
        ai_score: Optional[float] = None,
        ai_reason: Optional[str] = None,
    ) -> SourceProductLink:
        link = db.scalar(select(SourceProductLink).where(SourceProductLink.source_product_id == source_product_id))
        if link and link.locked and link.canonical_product_id != canonical_product_id:
            link.link_status = 'CONFLICT'
            db.commit()
            return link
        if not link:
            link = SourceProductLink(
                canonical_product_id=canonical_product_id,
                source_product_id=source_product_id,
                link_status=link_status,
                link_method=link_method,
                confidence_score=confidence_score,
                fuzzy_score=fuzzy_score,
                ai_score=ai_score,
                ai_reason=ai_reason,
            )
            db.add(link)
        else:
            link.canonical_product_id = canonical_product_id
            link.link_status = link_status
            link.link_method = link_method
            link.confidence_score = confidence_score
            link.fuzzy_score = fuzzy_score
            link.ai_score = ai_score
            link.ai_reason = ai_reason
            if link_status in {'APPROVED', 'AUTO_ACCEPTED'}:
                link.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(link)
        return link