from __future__ import annotations

from app.enums import LinkStatus
from app.models import CanonicalProduct, InventorySnapshot, SourceProduct, SourceProductLink, SourceSystem
from app.services.source_identity_service import SourceIdentityService, stable_source_key_for_product


class TestSourceIdentityBackfill:
    def test_detects_legacy_duplicate_shopify_inventory_rows(self, db):
        system = SourceSystem(code='SHOPIFY_INVENTORY', name='Shopify Inventory')
        db.add(system)
        db.flush()

        first = SourceProduct(
            source_system_id=system.id,
            source_record_key='panadol-500:SKU-PAN-20:Main Store 310A:1',
            title='Panadol 500mg Tablets 20',
            handle='panadol-500',
            sku='SKU-PAN-20',
            external_inventory_item_id='gid://shopify/InventoryItem/222',
            external_location_id='gid://shopify/Location/333',
            source_location_name='Main Store 310A',
        )
        second = SourceProduct(
            source_system_id=system.id,
            source_record_key='panadol-500:SKU-PAN-20:Main Store 310A:99',
            title='Panadol 500mg Tablets 20',
            handle='panadol-500',
            sku='SKU-PAN-20',
            external_inventory_item_id='gid://shopify/InventoryItem/222',
            external_location_id='gid://shopify/Location/333',
            source_location_name='Main Store 310A',
        )
        db.add_all([first, second])
        db.commit()

        service = SourceIdentityService()
        preview = service.preview_backfill(db)

        assert preview['group_count'] == 1
        assert preview['duplicate_count'] == 1
        assert preview['groups'][0]['stable_key'] == 'shopify-inventory:gid://shopify/InventoryItem/222:gid://shopify/Location/333'

    def test_apply_backfill_repoints_links_and_snapshots(self, db):
        system = SourceSystem(code='SHOPIFY_INVENTORY', name='Shopify Inventory')
        db.add(system)
        db.flush()

        survivor = SourceProduct(
            source_system_id=system.id,
            source_record_key='legacy:1',
            title='Panadol 500mg Tablets 20',
            handle='panadol-500',
            sku='SKU-PAN-20',
            external_inventory_item_id='gid://shopify/InventoryItem/222',
            external_location_id='gid://shopify/Location/333',
            source_location_name='Main Store 310A',
        )
        duplicate = SourceProduct(
            source_system_id=system.id,
            source_record_key='legacy:2',
            title='Panadol 500mg Tablets 20',
            handle='panadol-500',
            sku='SKU-PAN-20',
            external_inventory_item_id='gid://shopify/InventoryItem/222',
            external_location_id='gid://shopify/Location/333',
            source_location_name='Main Store 310A',
        )
        db.add_all([survivor, duplicate])
        db.flush()

        canonical = CanonicalProduct(canonical_name='Panadol 500mg Tablets 20', normalized_name='panadol 500mg tablets 20', review_status='NEEDS_REVIEW')
        db.add(canonical)
        db.flush()

        link = SourceProductLink(
            canonical_product_id=canonical.id,
            source_product_id=duplicate.id,
            link_status=LinkStatus.NEEDS_REVIEW,
            link_method='FUZZY_PLUS_AI',
        )
        snapshot = InventorySnapshot(
            source_product_id=duplicate.id,
            source_system_id=system.id,
            source_location='Main Store 310A',
            on_hand=4,
        )
        db.add_all([link, snapshot])
        db.commit()

        service = SourceIdentityService()
        groups = service.build_duplicate_groups(db)
        assert len(groups) == 1
        chosen_survivor_id = groups[0].survivor_id
        service.apply_backfill(db)

        updated_link = db.get(SourceProductLink, link.id)
        updated_snapshot = db.get(InventorySnapshot, snapshot.id)
        updated_duplicate = db.get(SourceProduct, duplicate.id)

        assert updated_link.source_product_id == chosen_survivor_id
        assert updated_snapshot.source_product_id == chosen_survivor_id

        retired_ids = {survivor.id, duplicate.id} - {chosen_survivor_id}
        assert len(retired_ids) == 1
        retired = db.get(SourceProduct, retired_ids.pop())
        assert retired is not None
        assert retired.is_active is False
        assert retired.status == 'MERGED_DUPLICATE'

    def test_stable_source_key_for_legacy_product_uses_new_shopify_identity(self, db):
        system = SourceSystem(code='SHOPIFY_PRODUCTS', name='Shopify Products')
        db.add(system)
        db.flush()

        product = SourceProduct(
            source_system_id=system.id,
            source_record_key='panadol-500:SKU-PAN-20:7',
            title='Panadol 500mg Tablets 20',
            handle='panadol-500',
            sku='SKU-PAN-20',
            external_variant_id='gid://shopify/ProductVariant/111',
        )
        db.add(product)
        db.commit()

        assert stable_source_key_for_product('SHOPIFY_PRODUCTS', product) == 'shopify-product-variant:gid://shopify/ProductVariant/111'
