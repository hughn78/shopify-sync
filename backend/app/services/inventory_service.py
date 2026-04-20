from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models import InventorySnapshot

logger = logging.getLogger(__name__)


class InventoryService:
    def create_snapshot(
        self,
        db: Session,
        source_product_id: Optional[int],
        source_system_id: int,
        import_batch_id: int,
        source_location: Optional[str],
        on_hand: Optional[int],
        available: Optional[int] = None,
        committed: Optional[int] = None,
        unavailable: Optional[int] = None,
        canonical_product_id: Optional[int] = None,
    ) -> InventorySnapshot:
        snapshot = InventorySnapshot(
            canonical_product_id=canonical_product_id,
            source_product_id=source_product_id,
            source_system_id=source_system_id,
            source_location=source_location,
            on_hand=on_hand,
            available=available,
            committed=committed,
            unavailable=unavailable,
            import_batch_id=import_batch_id,
        )
        db.add(snapshot)
        db.flush()
        db.refresh(snapshot)
        logger.debug('Created inventory snapshot id=%s source_product_id=%s on_hand=%s', snapshot.id, source_product_id, on_hand)
        return snapshot
