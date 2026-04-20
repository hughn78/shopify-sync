from __future__ import annotations

import pytest

from app.enums import LinkStatus
from app.models import (
    CanonicalProduct,
    InventorySnapshot,
    SourceProduct,
    SourceProductLink,
    SourceSystem,
)
from app.services.reconciliation_service import ReconciliationService


@pytest.fixture
def reconciliation_db(db):
    shopify_system = SourceSystem(code='SHOPIFY_INVENTORY', name='Shopify Inventory')
    fos_system = SourceSystem(code='FOS', name='FOS')
    db.add_all([shopify_system, fos_system])
    db.flush()

    canonical = CanonicalProduct(
        canonical_name='Paracetamol 500mg',
        normalized_name='paracetamol 500mg',
        review_status='NEEDS_REVIEW',
    )
    db.add(canonical)
    db.flush()

    shopify_product = SourceProduct(
        source_system_id=shopify_system.id,
        source_record_key='shopify:1',
        title='Paracetamol 500mg',
        handle='paracetamol-500mg',
        external_variant_id='gid://shopify/ProductVariant/111',
        external_inventory_item_id='gid://shopify/InventoryItem/222',
        external_location_id='gid://shopify/Location/333',
        source_location_name='Main Store 310A',
    )
    fos_product = SourceProduct(
        source_system_id=fos_system.id,
        source_record_key='fos:1',
        title='Paracetamol 500mg Tabs',
        apn='APN001',
    )
    db.add_all([shopify_product, fos_product])
    db.flush()

    db.add_all([
        SourceProductLink(
            canonical_product_id=canonical.id,
            source_product_id=shopify_product.id,
            link_status=LinkStatus.AUTO_ACCEPTED,
            link_method='EXACT_BARCODE',
        ),
        SourceProductLink(
            canonical_product_id=canonical.id,
            source_product_id=fos_product.id,
            link_status=LinkStatus.AUTO_ACCEPTED,
            link_method='EXACT_APN',
        ),
    ])
    db.flush()

    db.add_all([
        InventorySnapshot(
            source_product_id=shopify_product.id,
            source_system_id=shopify_system.id,
            on_hand=10,
            source_location='store',
        ),
        InventorySnapshot(
            source_product_id=fos_product.id,
            source_system_id=fos_system.id,
            on_hand=20,
            source_location='fos',
        ),
    ])
    db.commit()
    return db, canonical, shopify_product, fos_product


class TestReconciliationService:
    def test_creates_run(self, reconciliation_db):
        db, *_ = reconciliation_db
        svc = ReconciliationService()
        run = svc.run(db)
        assert run.id is not None

    def test_creates_reconciliation_rows(self, reconciliation_db):
        from app.models import InventoryReconciliationRow
        from sqlalchemy import select

        db, *_ = reconciliation_db
        svc = ReconciliationService()
        run = svc.run(db)
        rows = db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run.id)).all()
        assert len(rows) == 1

    def test_proposed_quantity_matches_fos_soh(self, reconciliation_db):
        from app.models import InventoryReconciliationRow
        from sqlalchemy import select

        db, *_ = reconciliation_db
        svc = ReconciliationService()
        run = svc.run(db)
        rows = db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run.id)).all()
        assert rows[0].fos_soh == 20
        assert rows[0].shopify_current_on_hand == 10
        assert rows[0].proposed_shopify_on_hand == 20

    def test_preserves_shopify_identity_fields(self, reconciliation_db):
        from app.models import InventoryReconciliationRow
        from sqlalchemy import select

        db, *_ = reconciliation_db
        svc = ReconciliationService()
        run = svc.run(db)
        rows = db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run.id)).all()
        assert rows[0].shopify_variant_id == 'gid://shopify/ProductVariant/111'
        assert rows[0].shopify_inventory_item_id == 'gid://shopify/InventoryItem/222'
        assert rows[0].shopify_location_id == 'gid://shopify/Location/333'
        assert rows[0].shopify_location_name == 'Main Store 310A'

    def test_large_delta_warning_flagged(self, reconciliation_db):
        from app.models import InventoryReconciliationRow
        from sqlalchemy import select

        db, *_ = reconciliation_db
        svc = ReconciliationService()
        run = svc.run(db)
        rows = db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run.id)).all()
        warnings = (rows[0].warning_flags_json or {}).get('warnings', [])
        assert 'LARGE_DELTA' in warnings

    def test_missing_source_product_skipped(self, db):
        from app.models import InventoryReconciliationRow
        from sqlalchemy import select

        canonical = CanonicalProduct(canonical_name='Ghost Product', normalized_name='ghost product', review_status='NEEDS_REVIEW')
        db.add(canonical)
        db.flush()
        # Link points to non-existent source product id
        db.add(SourceProductLink(
            canonical_product_id=canonical.id,
            source_product_id=99999,
            link_status=LinkStatus.AUTO_ACCEPTED,
            link_method='EXACT_BARCODE',
        ))
        db.commit()

        svc = ReconciliationService()
        run = svc.run(db)
        rows = db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run.id)).all()
        assert len(rows) == 0
