from __future__ import annotations

from app.enums import LinkStatus
from app.models import CanonicalProduct, ProductIdentifier, SourceProduct, SourceProductLink, SourceSystem
from app.services.canonical_product_service import CanonicalProductService
from app.services.identifier_service import IdentifierService
from app.services.review_service import ReviewService


class TestIdentifierEnrichment:
    def test_create_from_source_attaches_identifiers(self, db):
        system = SourceSystem(code='FOS', name='FOS')
        db.add(system)
        db.flush()

        source = SourceProduct(
            source_system_id=system.id,
            source_record_key='fos:1',
            title='Panadol 500mg Tablets 20',
            barcode='9300675001234',
            apn='12345',
            pde='PDE001',
            sku='SKU-PAN-20',
        )
        db.add(source)
        db.flush()

        canonical = CanonicalProductService().create_from_source(db, source, 'FOS')
        identifiers = db.query(ProductIdentifier).filter(ProductIdentifier.canonical_product_id == canonical.id).all()

        assert {item.identifier_type for item in identifiers} == {'BARCODE', 'APN', 'PDE', 'SKU'}
        assert canonical.primary_barcode == '9300675001234'
        assert canonical.primary_apn == '12345'
        assert canonical.primary_pde == 'PDE001'

    def test_review_approval_backfills_identifiers(self, db):
        system = SourceSystem(code='FOS', name='FOS')
        db.add(system)
        db.flush()

        canonical = CanonicalProduct(canonical_name='Panadol 500mg Tablets 20', normalized_name='panadol 500mg tablets 20', review_status='NEEDS_REVIEW')
        source = SourceProduct(
            source_system_id=system.id,
            source_record_key='fos:2',
            title='Panadol 500mg Tablets 20',
            barcode='9300675001234',
            apn='12345',
            pde='PDE001',
            sku='SKU-PAN-20',
        )
        db.add_all([canonical, source])
        db.flush()

        link = SourceProductLink(
            canonical_product_id=canonical.id,
            source_product_id=source.id,
            link_status=LinkStatus.NEEDS_REVIEW,
            link_method='FUZZY_PLUS_AI',
        )
        db.add(link)
        db.commit()

        ReviewService().apply_action(db, link, action='approve', note='Approve for identifier memory')

        identifiers = db.query(ProductIdentifier).filter(ProductIdentifier.canonical_product_id == canonical.id).all()
        assert {item.identifier_type for item in identifiers} == {'BARCODE', 'APN', 'PDE', 'SKU'}

    def test_identifier_backfill_populates_existing_links(self, db):
        system = SourceSystem(code='FOS', name='FOS')
        db.add(system)
        db.flush()

        canonical = CanonicalProduct(canonical_name='Ibuprofen 200mg', normalized_name='ibuprofen 200mg', review_status='NEEDS_REVIEW')
        source = SourceProduct(
            source_system_id=system.id,
            source_record_key='fos:3',
            title='Ibuprofen 200mg',
            barcode='5000158107709',
            apn='54321',
            sku='SKU-IBU-200',
        )
        db.add_all([canonical, source])
        db.flush()

        link = SourceProductLink(
            canonical_product_id=canonical.id,
            source_product_id=source.id,
            link_status=LinkStatus.APPROVED,
            link_method='EXACT_BARCODE',
        )
        db.add(link)
        db.commit()

        result = IdentifierService().backfill_identifiers_from_links(db)
        identifiers = db.query(ProductIdentifier).filter(ProductIdentifier.canonical_product_id == canonical.id).all()

        assert result['canonical_count'] == 1
        assert len(identifiers) == 3
        assert canonical.primary_barcode == '5000158107709'
        assert canonical.primary_apn == '54321'
