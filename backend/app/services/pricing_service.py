from __future__ import annotations
from typing import Dict, Optional

class PricingService:
    def compare_prices(self, shopify_price: Optional[float], fos_price: Optional[float]) -> Dict:
        if shopify_price is None or fos_price is None:
            return {'status': 'INSUFFICIENT_DATA'}
        return {
            'status': 'MATCH' if abs(shopify_price - fos_price) < 0.01 else 'DIFF',
            'difference': round(shopify_price - fos_price, 2),
        }