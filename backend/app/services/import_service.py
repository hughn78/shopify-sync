from __future__ import annotations

import csv
import hashlib
from io import BytesIO, StringIO
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.models import ImportBatch


FILE_COLUMN_HINTS = {
    'SHOPIFY_PRODUCTS': {'Handle', 'Title'},
    'SHOPIFY_INVENTORY': {'Handle', 'Title'},
    'FOS': {'APN', 'SOH'},
    'PRICEBOOK': {'Product', 'Wholesale Price'},
    'MASTERCATALOG': {'APN', 'Name'},
    'SCRAPED_CATALOG': {'name', 'slug', 'price'},
}


class ImportService:
    def detect_type(self, columns: Iterable[str], filename: str) -> str:
        normalized_columns = {str(column).strip() for column in columns if str(column).strip()}
        lower_columns = {column.lower() for column in normalized_columns}
        lower_name = filename.lower()

        if {'stock name', 'soh'}.issubset(lower_columns) or ('apn' in lower_columns and 'soh' in lower_columns):
            return 'FOS'

        if {'product', 'wholesale price'} & lower_columns and ('api pde' in lower_columns or 'wholesale price' in lower_columns):
            return 'PRICEBOOK'

        if {'description', 'price gst inc'} & lower_columns and ('pde' in lower_columns or 'barcode' in lower_columns):
            return 'PRICEBOOK'

        if 'name' in lower_columns and 'price' in lower_columns and ('category' in lower_columns or 'subcategory' in lower_columns):
            return 'MASTERCATALOG'

        if 'name' in lower_columns and 'slug' in lower_columns and 'price' in lower_columns:
            return 'SCRAPED_CATALOG'

        if 'location' in lower_columns and ({'sku', 'available'} & lower_columns or 'on hand' in ' '.join(lower_columns)):
            return 'SHOPIFY_INVENTORY'

        if 'variant sku' in lower_columns or 'variant barcode' in lower_columns or 'body (html)' in lower_columns:
            return 'SHOPIFY_PRODUCTS'

        if 'inventory' in lower_name:
            return 'SHOPIFY_INVENTORY'
        if 'product' in lower_name or 'products' in lower_name:
            return 'SHOPIFY_PRODUCTS'
        if 'fos' in lower_name or 'cleaned' in lower_name or 'stock' in lower_name:
            return 'FOS'
        if 'pricebook' in lower_name or 'price book' in lower_name:
            return 'PRICEBOOK'
        if 'mastercatalog' in lower_name or 'master catalog' in lower_name:
            return 'MASTERCATALOG'
        if 'scrape' in lower_name or 'scraped' in lower_name:
            return 'SCRAPED_CATALOG'

        for import_type, required in FILE_COLUMN_HINTS.items():
            if {value.lower() for value in required}.issubset(lower_columns):
                return import_type
        raise ValueError(f'Could not detect import type for {filename}. Columns seen: {sorted(normalized_columns)[:12]}')

    def parse_file(self, filename: str, content: bytes) -> Tuple[str, List[dict]]:
        suffix = Path(filename).suffix.lower()
        if suffix in {'.csv', '.txt'}:
            text = content.decode('utf-8-sig', errors='ignore')
            reader = csv.DictReader(StringIO(text))
            rows = [dict(row) for row in reader]
            detected = self.detect_type(reader.fieldnames or [], filename)
            return detected, rows
        if suffix in {'.xlsx', '.xlsm', '.xls'}:
            df = pd.read_excel(BytesIO(content))
            rows = df.fillna('').to_dict(orient='records')
            detected = self.detect_type(df.columns.tolist(), filename)
            return detected, rows
        raise ValueError(f'Unsupported file type: {suffix}')

    def file_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def create_batch(self, db: Session, import_type: str, filename: str, content: bytes, row_count: int) -> ImportBatch:
        batch = ImportBatch(
            import_type=import_type,
            filename=filename,
            file_hash=self.file_hash(content),
            row_count=row_count,
            status='IMPORTED',
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch
