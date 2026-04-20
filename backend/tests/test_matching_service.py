from __future__ import annotations

import pytest

from app.enums import LinkStatus
from app.models import CanonicalProduct, ProductIdentifier, SourceProduct, SourceSystem
from app.services.matching_service import MatchingService


@pytest.fixture
def match_db(db):
    system = SourceSystem(code='FOS', name='FOS')
    db.add(system)
    db.flush()
    return db, system


class TestMatchingService:
    def test_exact_identifier_match(self, match_db):
        db, system = match_db
        canonical = CanonicalProduct(canonical_name='Aspirin 300mg', normalized_name='aspirin 300mg', review_status='NEEDS_REVIEW')
        db.add(canonical)
        db.flush()

        db.add(ProductIdentifier(
            canonical_product_id=canonical.id,
            identifier_type='BARCODE',
            identifier_value='5000158107709',
            normalized_identifier_value='5000158107709',
            is_active=True,
        ))
        db.flush()

        source = SourceProduct(
            source_system_id=system.id,
            source_record_key='fos:barcode',
            title='Aspirin 300mg',
            normalized_title='aspirin 300mg',
            barcode='5000158107709',
        )
        db.add(source)
        db.flush()

        svc = MatchingService()
        link = svc.resolve_source_product(db, source)
        assert link.link_status == LinkStatus.AUTO_ACCEPTED
        assert link.canonical_product_id == canonical.id

    def test_exact_name_match(self, match_db):
        db, system = match_db
        canonical = CanonicalProduct(canonical_name='Ibuprofen 200mg', normalized_name='ibuprofen 200mg', review_status='NEEDS_REVIEW')
        db.add(canonical)
        db.flush()

        source = SourceProduct(
            source_system_id=system.id,
            source_record_key='fos:name',
            title='Ibuprofen 200mg',
            normalized_title='ibuprofen 200mg',
        )
        db.add(source)
        db.flush()

        svc = MatchingService()
        link = svc.resolve_source_product(db, source)
        assert link.link_status == LinkStatus.AUTO_ACCEPTED
        assert link.link_method == 'NORMALIZED_NAME'

    def test_no_match_creates_canonical(self, match_db):
        db, system = match_db
        source = SourceProduct(
            source_system_id=system.id,
            source_record_key='fos:new',
            title='Brand New Product XYZ',
            normalized_title='brand new product xyz',
        )
        db.add(source)
        db.flush()

        svc = MatchingService()
        link = svc.resolve_source_product(db, source)
        assert link.link_status == LinkStatus.NEEDS_REVIEW
        assert link.link_method == 'CREATED_NEW_CANONICAL'
        assert link.canonical_product_id is not None

    def test_locked_link_is_skipped(self, match_db):
        db, system = match_db
        canonical = CanonicalProduct(canonical_name='Product A', normalized_name='product a', review_status='NEEDS_REVIEW')
        canonical2 = CanonicalProduct(canonical_name='Product B', normalized_name='product b', review_status='NEEDS_REVIEW')
        db.add_all([canonical, canonical2])
        db.flush()

        source = SourceProduct(
            source_system_id=system.id,
            source_record_key='fos:locked',
            title='Product A',
            normalized_title='product a',
        )
        db.add(source)
        db.flush()

        from app.models import SourceProductLink
        locked_link = SourceProductLink(
            canonical_product_id=canonical.id,
            source_product_id=source.id,
            link_status=LinkStatus.APPROVED,
            link_method='NORMALIZED_NAME',
            locked=True,
        )
        db.add(locked_link)
        db.flush()

        svc = MatchingService()
        result = svc.resolve_source_product(db, source)
        assert result.id == locked_link.id
        assert result.locked is True
