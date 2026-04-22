from __future__ import annotations

from app.services.normalization_service import NormalizationService
from app.services.source_product_service import SourceProductService


def test_shopify_product_import_preserves_rich_catalog_fields_in_raw_payload(db):
    row = {
        'Handle': 'omura-x1-vaporiser-bundle',
        'Title': 'Omura X1 Vaporiser Bundle',
        'Body (HTML)': '<p>Bundle description</p>',
        'Vendor': 'Blackshaws Road Pharmacy',
        'Product Category': 'Home & Garden > Smoking Accessories',
        'Type': 'Vaporizer',
        'Tags': 'Vaporizer, Bundle',
        'Option1 Name': 'Title',
        'Option1 Value': 'Default Title',
        'Variant SKU': 'OMURA-X1',
        'Variant Barcode': '1234567890123',
        'Variant Price': '309.95',
        'Cost per item': '289.99',
        'Image Src': 'https://cdn.example.com/omura.webp',
        'Status': 'archived',
    }

    normalized = NormalizationService().normalize_source_row(row, 'SHOPIFY_PRODUCTS')
    source_product = SourceProductService().upsert_source_product(
        db,
        'SHOPIFY_PRODUCTS',
        'shopify-product:omura-x1-vaporiser-bundle:OMURA-X1',
        {**row, **normalized},
        batch_id=1,
    )

    assert source_product.handle == 'omura-x1-vaporiser-bundle'
    assert source_product.title == 'Omura X1 Vaporiser Bundle'
    assert source_product.vendor == 'Blackshaws Road Pharmacy'
    assert source_product.product_type == 'Vaporizer'
    assert source_product.status == 'archived'
    assert source_product.sku == 'OMURA-X1'
    assert source_product.barcode == '1234567890123'

    raw = source_product.raw_payload_json
    assert raw['Body (HTML)'] == '<p>Bundle description</p>'
    assert raw['Product Category'] == 'Home & Garden > Smoking Accessories'
    assert raw['Tags'] == 'Vaporizer, Bundle'
    assert raw['Variant Price'] == '309.95'
    assert raw['Cost per item'] == '289.99'
    assert raw['Image Src'] == 'https://cdn.example.com/omura.webp'


def test_normalization_extracts_shopify_product_ids_and_variant_fields():
    row = {
        'Product ID': 'gid://shopify/Product/999',
        'Variant ID': 'gid://shopify/ProductVariant/111',
        'Variant SKU': 'SKU-PROD-1',
        'Variant Barcode': '7350012554033',
        'Title': 'Bio-Practica BioGaia Prodentis 30 Tablets',
    }

    normalized = NormalizationService().normalize_source_row(row, 'SHOPIFY_PRODUCTS')

    assert normalized['external_product_id'] == 'gid://shopify/Product/999'
    assert normalized['external_variant_id'] == 'gid://shopify/ProductVariant/111'
    assert normalized['sku'] == 'SKU-PROD-1'
    assert normalized['barcode'] == '7350012554033'
    assert normalized['normalized_title'] == 'biopractica biogaia prodentis 30 tablets'
