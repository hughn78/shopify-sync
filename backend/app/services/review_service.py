from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.enums import LinkStatus, ProductReviewStatus, ReviewAction
from app.models import CanonicalProduct, ManualReviewAction, SourceProductLink

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ReviewService:
    def apply_action(
        self,
        db: Session,
        link: SourceProductLink,
        action: str,
        note: Optional[str],
        canonical_product_id: Optional[int] = None,
        locked: Optional[bool] = None,
        commit: bool = True,
    ):
        old = {
            'link_status': link.link_status,
            'canonical_product_id': link.canonical_product_id,
            'locked': link.locked,
        }
        if action == ReviewAction.APPROVE:
            link.link_status = LinkStatus.APPROVED
            link.excluded = False
            link.approved_at = _utcnow()
        elif action == ReviewAction.REJECT:
            link.link_status = LinkStatus.REJECTED
            link.excluded = False
        elif action == ReviewAction.EXCLUDE:
            link.link_status = LinkStatus.EXCLUDED
            link.excluded = True
        elif action == ReviewAction.REASSIGN and canonical_product_id:
            link.canonical_product_id = canonical_product_id
            link.link_status = LinkStatus.APPROVED
            link.excluded = False
        elif action == ReviewAction.CREATE_CANONICAL:
            canonical = CanonicalProduct(
                canonical_name=f'Manual Canonical {link.source_product_id}',
                normalized_name=f'manual canonical {link.source_product_id}',
                review_status=ProductReviewStatus.APPROVED,
                created_from_source='MANUAL',
                confidence_summary='Created during review',
            )
            db.add(canonical)
            db.flush()
            link.canonical_product_id = canonical.id
            link.link_status = LinkStatus.APPROVED
            link.excluded = False

        if locked is not None:
            link.locked = locked
        if note:
            link.review_notes = note

        db.add(
            ManualReviewAction(
                entity_type='source_product_link',
                entity_id=str(link.id),
                action_type=action,
                old_value_json=old,
                new_value_json={
                    'link_status': link.link_status,
                    'canonical_product_id': link.canonical_product_id,
                    'locked': link.locked,
                },
                user_note=note,
            )
        )
        logger.info('Review action=%s link_id=%s', action, link.id)
        if commit:
            db.commit()
            db.refresh(link)
        return link

    def apply_bulk_action(
        self,
        db: Session,
        links: List[SourceProductLink],
        action: str,
        note: Optional[str],
        canonical_product_id: Optional[int] = None,
        locked: Optional[bool] = None,
    ):
        updated_links = []
        for link in links:
            updated_links.append(
                self.apply_action(
                    db,
                    link,
                    action,
                    note,
                    canonical_product_id=canonical_product_id,
                    locked=locked,
                    commit=False,
                )
            )
        db.commit()
        for link in updated_links:
            db.refresh(link)
        logger.info('Bulk review action=%s applied to %d links', action, len(updated_links))
        return updated_links
