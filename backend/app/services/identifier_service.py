from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProductIdentifier
from app.utils.normalizers import normalize_identifier


class IdentifierService:
    def resolve_exact_identifier(self, db: Session, identifier_type: str, identifier_value: str | None):
        normalized = normalize_identifier(identifier_value)
        if not normalized:
            return None
        return db.scalar(
            select(ProductIdentifier).where(
                ProductIdentifier.identifier_type == identifier_type,
                ProductIdentifier.normalized_identifier_value == normalized,
                ProductIdentifier.is_active.is_(True),
            )
        )

    def attach_identifier(self, db: Session, canonical_product_id: int, identifier_type: str, identifier_value: str, source: str, is_primary: bool = False):
        normalized = normalize_identifier(identifier_value)
        if not normalized:
            return None
        existing = db.scalar(
            select(ProductIdentifier).where(
                ProductIdentifier.canonical_product_id == canonical_product_id,
                ProductIdentifier.identifier_type == identifier_type,
                ProductIdentifier.normalized_identifier_value == normalized,
            )
        )
        if existing:
            existing.is_active = True
            existing.is_primary = existing.is_primary or is_primary
            existing.last_seen_at = existing.last_seen_at
            db.commit()
            return existing
        item = ProductIdentifier(
            canonical_product_id=canonical_product_id,
            identifier_type=identifier_type,
            identifier_value=identifier_value,
            normalized_identifier_value=normalized,
            source=source,
            is_primary=is_primary,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
