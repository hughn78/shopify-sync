from __future__ import annotations

from app.utils.normalizers import normalize_blank, normalize_identifier, normalize_location, normalize_name_for_match


class NormalizationService:
    def normalize_source_row(self, row: dict, source_type: str) -> dict:
        normalized = dict(row)
        normalized['normalized_title'] = normalize_name_for_match(
            row.get('Title') or row.get('title') or row.get('name') or row.get('Name') or row.get('Product') or row.get('Description') or row.get('Stock Name') or row.get('Full Name')
        )
        normalized['barcode'] = normalize_identifier(row.get('Variant Barcode') or row.get('Barcode') or row.get('barcode'))
        normalized['apn'] = normalize_identifier(row.get('APN') or row.get('apn'))
        normalized['pde'] = normalize_identifier(row.get('PDE') or row.get('pde') or row.get('API PDE'))
        normalized['sku'] = normalize_blank(row.get('Variant SKU') or row.get('SKU') or row.get('sku'))
        normalized['location'] = normalize_location(row.get('Location') or row.get('location'))
        return normalized
