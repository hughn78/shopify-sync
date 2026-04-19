from __future__ import annotations
from typing import Optional

class BarcodeService:
    def suggest_barcode_update(self, current_barcode: Optional[str], approved_apn: Optional[str]) -> Optional[str]:
        if current_barcode:
            return current_barcode
        return approved_apn