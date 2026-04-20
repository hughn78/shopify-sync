from __future__ import annotations
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CanonicalProduct, ProductIdentifier, SourceProduct, SourceProductLink
from app.utils.normalizers import normalize_identifier


class IdentifierService:
    def resolve_exact_identifier(self, db: Session, identifier_type: str, identifier_value: Optional[str]):
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
        return item

    def attach_identifiers_from_source_product(
        self,
        db: Session,
        canonical_product_id: int,
        source_product: SourceProduct,
        source: str,
        promote_primary: bool = False,
    ) -> list[ProductIdentifier]:
        attached: list[ProductIdentifier] = []
        for identifier_type, value, is_primary in [
            ('BARCODE', source_product.barcode, promote_primary),
            ('APN', source_product.apn, promote_primary),
            ('PDE', source_product.pde, promote_primary),
            ('SKU', source_product.sku, False),
        ]:
            identifier = self.attach_identifier(
                db,
                canonical_product_id=canonical_product_id,
                identifier_type=identifier_type,
                identifier_value=value,
                source=source,
                is_primary=is_primary,
            ) if value else None
            if identifier:
                attached.append(identifier)

        canonical = db.get(CanonicalProduct, canonical_product_id)
        if canonical:
            if source_product.barcode and not canonical.primary_barcode:
                canonical.primary_barcode = normalize_identifier(source_product.barcode)
            if source_product.apn and not canonical.primary_apn:
                canonical.primary_apn = normalize_identifier(source_product.apn)
            if source_product.pde and not canonical.primary_pde:
                canonical.primary_pde = normalize_identifier(source_product.pde)
        db.flush()
        return attached

    def backfill_identifiers_from_links(self, db: Session) -> dict:
        links = db.scalars(select(SourceProductLink)).all()
        attached = 0
        canonical_ids: set[int] = set()
        for link in links:
            source_product = db.get(SourceProduct, link.source_product_id)
            if source_product is None:
                continue
            identifiers = self.attach_identifiers_from_source_product(
                db,
                canonical_product_id=link.canonical_product_id,
                source_product=source_product,
                source=f'LINK:{link.link_status}',
                promote_primary=link.link_status in {'APPROVED', 'AUTO_ACCEPTED'},
            )
            attached += len(identifiers)
            canonical_ids.add(link.canonical_product_id)
        db.commit()
        return {
            'canonical_count': len(canonical_ids),
            'identifier_rows_touched': attached,
        }
