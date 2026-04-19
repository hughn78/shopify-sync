from __future__ import annotations

class BarcodeService:
    def suggest_barcode_update(self, current_barcode: str | None, approved_apn: str | None) -> str | None:
        if current_barcode:
            return current_barcode
        return approved_apn
