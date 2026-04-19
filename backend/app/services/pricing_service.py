class PricingService:
    def compare_prices(self, shopify_price: float | None, fos_price: float | None) -> dict:
        if shopify_price is None or fos_price is None:
            return {'status': 'INSUFFICIENT_DATA'}
        return {
            'status': 'MATCH' if abs(shopify_price - fos_price) < 0.01 else 'DIFF',
            'difference': round(shopify_price - fos_price, 2),
        }
