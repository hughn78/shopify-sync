from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import ExportRun, InventoryReconciliationRow, SourceProductLink
from app.services.export_service import ExportService
from app.services.import_service import ImportService
from app.services.inventory_service import InventoryService
from app.services.matching_service import MatchingService
from app.services.normalization_service import NormalizationService
from app.services.reconciliation_service import ReconciliationService
from app.services.review_service import ReviewService
from app.services.source_product_service import SourceProductService

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = ROOT / 'sample_data'


def coerce_int(value):
    if value in (None, ''):
        return None
    return int(float(value))


def main() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    import_service = ImportService()
    normalization_service = NormalizationService()
    source_product_service = SourceProductService()
    inventory_service = InventoryService()
    matching_service = MatchingService()
    review_service = ReviewService()
    reconciliation_service = ReconciliationService()
    export_service = ExportService()

    files = [
        SAMPLE_DIR / 'shopify_products_sample.csv',
        SAMPLE_DIR / 'shopify_inventory_sample.csv',
        SAMPLE_DIR / 'fos_stock_sample.xlsx',
    ]

    with SessionLocal() as db:
        for file in files:
            content = file.read_bytes()
            detected_type, rows = import_service.parse_file(file.name, content)
            batch = import_service.create_batch(db, detected_type, file.name, content, len(rows))
            system = source_product_service.get_source_system(db, detected_type)

            for idx, row in enumerate(rows, start=1):
                normalized = normalization_service.normalize_source_row(row, detected_type)
                if detected_type == 'SHOPIFY_PRODUCTS':
                    key = f"{row.get('Handle', '')}:{row.get('Variant SKU', '')}:{idx}"
                elif detected_type == 'SHOPIFY_INVENTORY':
                    key = f"{row.get('Handle', '')}:{row.get('SKU', '')}:{row.get('Location', '')}:{idx}"
                else:
                    key = f"{row.get('APN', '')}:{row.get('PDE', '')}:{idx}"
                source_product = source_product_service.upsert_source_product(db, detected_type, key, {**row, **normalized}, batch.id)

                if detected_type == 'SHOPIFY_INVENTORY':
                    inventory_service.create_snapshot(
                        db,
                        source_product_id=source_product.id,
                        source_system_id=system.id,
                        import_batch_id=batch.id,
                        source_location=normalized.get('location'),
                        on_hand=coerce_int(row.get('On hand (current)')),
                        available=coerce_int(row.get('Available')),
                        committed=coerce_int(row.get('Committed')),
                        unavailable=coerce_int(row.get('Unavailable')),
                    )
                elif detected_type == 'FOS':
                    inventory_service.create_snapshot(
                        db,
                        source_product_id=source_product.id,
                        source_system_id=system.id,
                        import_batch_id=batch.id,
                        source_location='fos',
                        on_hand=coerce_int(row.get('SOH')),
                    )

                matching_service.resolve_source_product(db, source_product)

        review_links = db.scalars(select(SourceProductLink).where(SourceProductLink.link_status == 'NEEDS_REVIEW')).all()
        for link in review_links:
            review_service.apply_action(db, link, action='approve', note='Approved during sample automation', locked=True)

        run = reconciliation_service.run(db)
        inventory_export = export_service.export_inventory_sync(db, run.id)
        unresolved_export = export_service.export_link_report(db, 'NEEDS_REVIEW', 'unresolved_links')
        approved_export = export_service.export_link_report(db, 'APPROVED', 'approved_links')

        recon_count = len(db.scalars(select(InventoryReconciliationRow).where(InventoryReconciliationRow.run_id == run.id)).all())
        export_count = len(db.scalars(select(ExportRun)).all())

        print('Sample flow complete')
        print(f'Reconciliation run: {run.id}')
        print(f'Reconciliation rows: {recon_count}')
        print(f'Inventory export: {inventory_export}')
        print(f'Unresolved export: {unresolved_export}')
        print(f'Approved export: {approved_export}')
        print(f'Export runs logged: {export_count}')


if __name__ == '__main__':
    main()
