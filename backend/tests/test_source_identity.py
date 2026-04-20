from __future__ import annotations

from app.main import _build_source_key
from app.models import SourceProduct, SourceSystem
from app.services.source_product_service import SourceProductService


def test_shopify_inventory_source_key_uses_inventory_item_and_location_ids():
    row = {
        'Handle': 'panadol-500',
        'SKU': 'SKU-PAN-20',
        'Inventory Item ID': 'gid://shopify/InventoryItem/222',
        'Location ID': 'gid://shopify/Location/333',
        'Location': 'Main Store 310A',
    }
    key = _build_source_key('SHOPIFY_INVENTORY', row, 1)
    assert key == 'shopify-inventory:gid://shopify/InventoryItem/222:gid://shopify/Location/333'


def test_shopify_inventory_source_key_is_stable_when_row_position_changes():
    row = {
        'SKU': 'SKU-PAN-20',
        'Inventory Item ID': 'gid://shopify/InventoryItem/222',
        'Location ID': 'gid://shopify/Location/333',
    }
    key_a = _build_source_key('SHOPIFY_INVENTORY', row, 1)
    key_b = _build_source_key('SHOPIFY_INVENTORY', row, 999)
    assert key_a == key_b


def test_shopify_product_source_key_uses_variant_id_when_present():
    row = {
        'Handle': 'panadol-500',
        'Variant SKU': 'SKU-PAN-20',
        'Variant ID': 'gid://shopify/ProductVariant/111',
    }
    key = _build_source_key('SHOPIFY_PRODUCTS', row, 4)
    assert key == 'shopify-product-variant:gid://shopify/ProductVariant/111'


def test_fos_source_key_prefers_apn_without_row_index():
    row = {'APN': '12345', 'PDE': 'ABC'}
    assert _build_source_key('FOS', row, 1) == 'fos-apn:12345'
    assert _build_source_key('FOS', row, 99) == 'fos-apn:12345'


def test_upsert_source_product_reuses_stable_key(db):
    system = SourceSystem(code='SHOPIFY_INVENTORY', name='Shopify Inventory')
    db.add(system)
    db.commit()

    service = SourceProductService()
    key = 'shopify-inventory:gid://shopify/InventoryItem/222:gid://shopify/Location/333'
    payload = {
        'Title': 'Panadol 500mg Tablets 20',
        'SKU': 'SKU-PAN-20',
        'external_inventory_item_id': 'gid://shopify/InventoryItem/222',
        'external_location_id': 'gid://shopify/Location/333',
        'source_location_name': 'Main Store 310A',
    }

    first = service.upsert_source_product(db, 'SHOPIFY_INVENTORY', key, payload, batch_id=1)
    second = service.upsert_source_product(db, 'SHOPIFY_INVENTORY', key, payload, batch_id=2)

    assert first.id == second.id
    products = db.query(SourceProduct).all()
    assert len(products) == 1
