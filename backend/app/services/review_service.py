from __future__ import annotations
from typing import List, Optional

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import CanonicalProduct, ManualReviewAction, SourceProductLink


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
        if action == 'approve':
            link.link_status = 'APPROVED'
            link.excluded = False
            link.approved_at = datetime.utcnow()
        elif action == 'reject':
            link.link_status = 'REJECTED'
            link.excluded = False
        elif action == 'exclude':
            link.link_status = 'EXCLUDED'
            link.excluded = True
        elif action == 'reassign' and canonical_product_id:
            link.canonical_product_id = canonical_product_id
            link.link_status = 'APPROVED'
            link.excluded = False
        elif action == 'create_canonical':
            canonical = CanonicalProduct(
                canonical_name=f'Manual Canonical {link.source_product_id}',
                normalized_name=f'manual canonical {link.source_product_id}',
                review_status='APPROVED',
                created_from_source='MANUAL',
                confidence_summary='Created during review',
            )
            db.add(canonical)
            db.flush()
            link.canonical_product_id = canonical.id
            link.link_status = 'APPROVED'
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
        return updated_links
