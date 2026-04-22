from __future__ import annotations

import pandas as pd

from app.enums import LinkStatus
from app.models import (
    CanonicalProduct,
    InventorySnapshot,
    SourceProduct,
    SourceProductLink,
    SourceSystem,
)
from app.services.export_service import ExportService
from app.services.reconciliation_service import ReconciliationService


def _build_db_for_export(db, missing_location: bool = False, review_row: bool = False):
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
        external_location_id=None if missing_location else 'gid://shopify/Location/333',
        source_location_name='Main Store 310A',
        sku='SKU-PAN-20',
        barcode='9300675001234',
    )
    fos_product = SourceProduct(
        source_system_id=fos_system.id,
        source_record_key='fos:1',
        title='Paracetamol 500mg Tabs',
        apn='APN001',
    )
    db.add_all([shopify_product, fos_product])
    db.flush()

    shopify_link_status = LinkStatus.AUTO_ACCEPTED
    fos_link_status = LinkStatus.NEEDS_REVIEW if review_row else LinkStatus.AUTO_ACCEPTED
    db.add_all([
        SourceProductLink(
            canonical_product_id=canonical.id,
            source_product_id=shopify_product.id,
            link_status=shopify_link_status,
            link_method='EXACT_BARCODE',
        ),
        SourceProductLink(
            canonical_product_id=canonical.id,
            source_product_id=fos_product.id,
            link_status=fos_link_status,
            link_method='EXACT_APN',
        ),
    ])
    db.flush()

    db.add_all([
        InventorySnapshot(
            source_product_id=shopify_product.id,
            source_system_id=shopify_system.id,
            on_hand=4,
            source_location='Main Store 310A',
        ),
        InventorySnapshot(
            source_product_id=fos_product.id,
            source_system_id=fos_system.id,
            on_hand=7,
            source_location='fos',
        ),
    ])
    db.commit()

    run = ReconciliationService().run(db)
    return run


class TestExportService:
    def test_shopify_upload_bundle_splits_safe_and_exception_rows(self, db, tmp_path, monkeypatch):
        run = _build_db_for_export(db)
        monkeypatch.setattr('app.services.export_service.EXPORT_DIR', tmp_path)

        result = ExportService().export_shopify_upload_bundle(db, run.id)

        safe_df = pd.read_csv(result['safe_upload_path'])
        exceptions_df = pd.read_csv(result['exceptions_path'])

        assert result['safe_count'] == 1
        assert result['exception_count'] == 0
        assert len(safe_df) == 1
        assert exceptions_df.empty
        assert list(safe_df.columns) == [
            'Handle',
            'Title',
            'Option1 Name',
            'Option1 Value',
            'Option2 Name',
            'Option2 Value',
            'Option3 Name',
            'Option3 Value',
            'SKU',
            'HS Code',
            'COO',
            'Location',
            'Bin name',
            'Incoming (not editable)',
            'Unavailable (not editable)',
            'Committed (not editable)',
            'Available (not editable)',
            'On hand (current)',
            'On hand (new)',
            'Variant ID',
            'Inventory Item ID',
            'Location ID',
            'Barcode',
            'Delta',
        ]
        assert safe_df.iloc[0]['Option1 Name'] == 'Title'
        assert safe_df.iloc[0]['Option1 Value'] == 'Default Title'
        assert safe_df.iloc[0]['Inventory Item ID'] == 'gid://shopify/InventoryItem/222'
        assert safe_df.iloc[0]['Location'] == 'Main Store 310A'
        assert safe_df.iloc[0]['Incoming (not editable)'] == 0
        assert safe_df.iloc[0]['Available (not editable)'] == 4
        assert safe_df.iloc[0]['On hand (current)'] == 4
        assert safe_df.iloc[0]['On hand (new)'] == 7

    def test_shopify_upload_bundle_blocks_missing_location_id(self, db, tmp_path, monkeypatch):
        run = _build_db_for_export(db, missing_location=True)
        monkeypatch.setattr('app.services.export_service.EXPORT_DIR', tmp_path)

        result = ExportService().export_shopify_upload_bundle(db, run.id)
        safe_df = pd.read_csv(result['safe_upload_path'])
        exceptions_df = pd.read_csv(result['exceptions_path'])

        assert result['safe_count'] == 0
        assert result['exception_count'] == 1
        assert safe_df.empty
        assert 'MISSING_SHOPIFY_LOCATION_ID' in exceptions_df.iloc[0]['Blockers']

    def test_shopify_upload_bundle_blocks_review_rows(self, db, tmp_path, monkeypatch):
        run = _build_db_for_export(db, review_row=True)
        monkeypatch.setattr('app.services.export_service.EXPORT_DIR', tmp_path)

        result = ExportService().export_shopify_upload_bundle(db, run.id)
        exceptions_df = pd.read_csv(result['exceptions_path'])

        assert result['safe_count'] == 0
        assert result['exception_count'] == 1
        assert 'SYNC_STATUS_NOT_READY' in exceptions_df.iloc[0]['Blockers']

    def test_shopify_products_bundle_splits_safe_and_exception_rows(self, db, tmp_path, monkeypatch):
        system = SourceSystem(code='SHOPIFY_PRODUCTS', name='Shopify Products')
        db.add(system)
        db.flush()

        canonical = CanonicalProduct(
            canonical_name='Omura X1 Vaporiser Bundle',
            normalized_name='omura x1 vaporiser bundle',
            review_status='NEEDS_REVIEW',
        )
        db.add(canonical)
        db.flush()

        safe_product = SourceProduct(
            source_system_id=system.id,
            source_record_key='shopify-product-variant:gid://shopify/ProductVariant/111',
            title='Omura X1 Vaporiser Bundle',
            handle='omura-x1-vaporiser-bundle',
            external_variant_id='gid://shopify/ProductVariant/111',
            sku='OMURA-X1',
            barcode='1234567890123',
            status='archived',
            raw_payload_json={
                'Handle': 'omura-x1-vaporiser-bundle',
                'Title': 'Omura X1 Vaporiser Bundle',
                'Body (HTML)': '<p>Bundle description</p>',
                'Vendor': 'Blackshaws Road Pharmacy',
                'Variant SKU': 'OMURA-X1',
                'Variant Barcode': '1234567890123',
                'Variant Price': '309.95',
                'Status': 'archived',
            },
        )
        exception_product = SourceProduct(
            source_system_id=system.id,
            source_record_key='shopify-product-variant:gid://shopify/ProductVariant/222',
            title='Broken Product',
            handle='broken-product',
            external_variant_id='gid://shopify/ProductVariant/222',
            sku=None,
            status='draft',
            raw_payload_json={
                'Handle': 'broken-product',
                'Title': 'Broken Product',
                'Vendor': 'Blackshaws Road Pharmacy',
                'Status': 'draft',
            },
        )
        db.add_all([safe_product, exception_product])
        db.flush()

        db.add_all([
            SourceProductLink(
                canonical_product_id=canonical.id,
                source_product_id=safe_product.id,
                link_status=LinkStatus.AUTO_ACCEPTED,
                link_method='EXACT_BARCODE',
            ),
            SourceProductLink(
                canonical_product_id=canonical.id,
                source_product_id=exception_product.id,
                link_status=LinkStatus.NEEDS_REVIEW,
                link_method='FUZZY_PLUS_AI',
            ),
        ])
        db.commit()

        monkeypatch.setattr('app.services.export_service.EXPORT_DIR', tmp_path)

        result = ExportService().export_shopify_products_bundle(db)

        safe_df = pd.read_csv(result['safe_products_path'])
        exceptions_df = pd.read_csv(result['exceptions_path'])

        assert result['safe_count'] == 1
        assert result['exception_count'] == 1
        assert safe_df.iloc[0]['Handle'] == 'omura-x1-vaporiser-bundle'
        assert safe_df.iloc[0]['Variant SKU'] == 'OMURA-X1'
        assert 'MISSING_VARIANT_SKU' in exceptions_df.iloc[0]['Blockers']
        assert 'MISSING_PRICE' in exceptions_df.iloc[0]['Blockers']
        assert 'MISSING_BODY_HTML' in exceptions_df.iloc[0]['Blockers']
