from __future__ import annotations

from app.models import SourceProduct, SourceSystem
from app.services.export_service import ExportService


def test_project_shopify_product_row_prefers_raw_payload_fields(db):
    system = SourceSystem(code='SHOPIFY_PRODUCTS', name='Shopify Products')
    db.add(system)
    db.flush()

    source_product = SourceProduct(
        source_system_id=system.id,
        source_record_key='shopify-product-variant:gid://shopify/ProductVariant/111',
        title='Fallback Title',
        handle='fallback-handle',
        sku='FALLBACK-SKU',
        barcode='9999999999999',
        vendor='Fallback Vendor',
        product_type='Fallback Type',
        status='draft',
        raw_payload_json={
            'Handle': 'omura-x1-vaporiser-bundle',
            'Title': 'Omura X1 Vaporiser Bundle',
            'Body (HTML)': '<p>Bundle description</p>',
            'Vendor': 'Blackshaws Road Pharmacy',
            'Product Category': 'Home & Garden > Smoking Accessories',
            'Type': 'Vaporizer',
            'Tags': 'Vaporizer, Bundle',
            'Published': False,
            'Option1 Name': 'Title',
            'Option1 Value': 'Default Title',
            'Variant SKU': 'OMURA-X1',
            'Variant Barcode': '1234567890123',
            'Variant Price': '309.95',
            'Cost per item': '289.99',
            'Image Src': 'https://cdn.example.com/omura.webp',
            'Status': 'archived',
        },
    )
    db.add(source_product)
    db.commit()

    row = ExportService().project_shopify_product_row(source_product)

    assert row == {
        'Handle': 'omura-x1-vaporiser-bundle',
        'Title': 'Omura X1 Vaporiser Bundle',
        'Body (HTML)': '<p>Bundle description</p>',
        'Vendor': 'Blackshaws Road Pharmacy',
        'Product Category': 'Home & Garden > Smoking Accessories',
        'Type': 'Vaporizer',
        'Tags': 'Vaporizer, Bundle',
        'Published': False,
        'Option1 Name': 'Title',
        'Option1 Value': 'Default Title',
        'Option2 Name': None,
        'Option2 Value': None,
        'Option3 Name': None,
        'Option3 Value': None,
        'Variant SKU': 'OMURA-X1',
        'Variant Barcode': '1234567890123',
        'Variant Price': '309.95',
        'Cost per item': '289.99',
        'Image Src': 'https://cdn.example.com/omura.webp',
        'Status': 'archived',
    }


def test_project_shopify_product_row_falls_back_to_structured_source_fields(db):
    system = SourceSystem(code='SHOPIFY_PRODUCTS', name='Shopify Products')
    db.add(system)
    db.flush()

    source_product = SourceProduct(
        source_system_id=system.id,
        source_record_key='shopify-product-variant:gid://shopify/ProductVariant/222',
        title='Bio-Practica BioGaia Prodentis 30 Tablets',
        handle='bio-practica-biogaia-prodentis-30-tablets',
        sku='BTPROD30',
        barcode='7350012554033',
        vendor='Blackshaws Road Pharmacy',
        product_type='General Health',
        status='draft',
        raw_payload_json={},
    )
    db.add(source_product)
    db.commit()

    row = ExportService().project_shopify_product_row(source_product)

    assert row['Handle'] == 'bio-practica-biogaia-prodentis-30-tablets'
    assert row['Title'] == 'Bio-Practica BioGaia Prodentis 30 Tablets'
    assert row['Vendor'] == 'Blackshaws Road Pharmacy'
    assert row['Type'] == 'General Health'
    assert row['Variant SKU'] == 'BTPROD30'
    assert row['Variant Barcode'] == '7350012554033'
    assert row['Status'] == 'draft'
    assert row['Option1 Name'] == 'Title'
    assert row['Option1 Value'] == 'Default Title'
