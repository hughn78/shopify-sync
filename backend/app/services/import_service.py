from __future__ import annotations

import csv
import hashlib
from io import BytesIO, StringIO
from pathlib import Path
from typing import Iterable, List

import pandas as pd
from sqlalchemy.orm import Session

from app.models import ImportBatch


FILE_COLUMN_HINTS = {
    'SHOPIFY_PRODUCTS': {'Handle', 'Title', 'Variant SKU', 'Variant Barcode'},
    'SHOPIFY_INVENTORY': {'Handle', 'Title', 'SKU', 'Location'},
    'FOS': {'Stock Name', 'Full Name', 'APN', 'SOH'},
}


class ImportService:
    def detect_type(self, columns: Iterable[str], filename: str) -> str:
        colset = set(columns)
        for import_type, required in FILE_COLUMN_HINTS.items():
            if required.issubset(colset):
                return import_type
        lower_name = filename.lower()
        if 'inventory' in lower_name:
            return 'SHOPIFY_INVENTORY'
        if 'product' in lower_name:
            return 'SHOPIFY_PRODUCTS'
        return 'FOS'

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
