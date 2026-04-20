from __future__ import annotations

import csv
import io

import pytest

from app.services.import_service import ImportService, MAX_UPLOAD_BYTES

service = ImportService()


def _csv_bytes(*rows: dict) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode()


class TestValidateUpload:
    def test_rejects_oversized_file(self):
        big = b'x' * (MAX_UPLOAD_BYTES + 1)
        with pytest.raises(ValueError, match='exceeds'):
            service.validate_upload('big.csv', big)

    def test_rejects_unsupported_extension(self):
        with pytest.raises(ValueError, match='Unsupported'):
            service.validate_upload('data.pdf', b'content')

    def test_accepts_valid_csv(self):
        service.validate_upload('data.csv', b'col1,col2\n1,2')

    def test_accepts_xlsx(self):
        service.validate_upload('data.xlsx', b'placeholder')


class TestDetectType:
    def test_fos_by_columns(self):
        assert service.detect_type(['APN', 'SOH', 'Stock Name'], 'data.csv') == 'FOS'

    def test_shopify_inventory_by_columns(self):
        assert service.detect_type(['Handle', 'Title', 'Location', 'SKU', 'Available'], 'inventory.csv') == 'SHOPIFY_INVENTORY'

    def test_shopify_products_by_column(self):
        assert service.detect_type(['Handle', 'Title', 'Variant SKU', 'Variant Barcode'], 'products.csv') == 'SHOPIFY_PRODUCTS'

    def test_fos_by_filename(self):
        assert service.detect_type(['col1', 'col2'], 'fos_stock.csv') == 'FOS'

    def test_pricebook_by_filename(self):
        assert service.detect_type(['col1', 'col2'], 'pricebook_jan.csv') == 'PRICEBOOK'

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match='Could not detect'):
            service.detect_type(['foo', 'bar'], 'unknown.csv')


class TestParseFile:
    def test_parses_csv(self):
        content = _csv_bytes({'APN': '123', 'SOH': '10'}, {'APN': '456', 'SOH': '5'})
        detected, rows = service.parse_file('fos_data.csv', content)
        assert detected == 'FOS'
        assert len(rows) == 2
        assert rows[0]['APN'] == '123'

    def test_rejects_bad_extension(self):
        with pytest.raises(ValueError):
            service.parse_file('data.pdf', b'content')

    def test_csv_latin1_fallback(self):
        content = 'APN,SOH\n123,10\n456\xe9,5\n'.encode('latin-1')
        detected, rows = service.parse_file('fos.csv', content)
        assert len(rows) == 2
