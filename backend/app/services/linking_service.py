from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import LinkStatus
from app.models import SourceProductLink

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
            link.link_status = LinkStatus.CONFLICT
            db.flush()
            logger.warning('Link id=%s is locked and conflicts with canonical_product_id=%s', link.id, canonical_product_id)
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
            logger.debug('Created link source_product_id=%s canonical_product_id=%s status=%s', source_product_id, canonical_product_id, link_status)
        else:
            link.canonical_product_id = canonical_product_id
            link.link_status = link_status
            link.link_method = link_method
            link.confidence_score = confidence_score
            link.fuzzy_score = fuzzy_score
            link.ai_score = ai_score
            link.ai_reason = ai_reason
            if link_status in {LinkStatus.APPROVED, LinkStatus.AUTO_ACCEPTED}:
                link.approved_at = _utcnow()
            logger.debug('Updated link id=%s status=%s', link.id, link_status)
        db.flush()
        db.refresh(link)
        return link
