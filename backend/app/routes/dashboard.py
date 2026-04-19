from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CanonicalProduct, ExportRun, ImportBatch, InventoryReconciliationRow, SourceProduct, SourceProductLink, SourceSystem
from app.schemas import DashboardSummary


def get_dashboard_summary(db: Session) -> DashboardSummary:
    shopify_systems = db.scalars(select(SourceSystem.id).where(SourceSystem.code.in_(['SHOPIFY_PRODUCTS', 'SHOPIFY_INVENTORY']))).all()
    fos_systems = db.scalars(select(SourceSystem.id).where(SourceSystem.code == 'FOS')).all()

    return DashboardSummary(
        canonical_products=db.scalar(select(func.count()).select_from(CanonicalProduct)) or 0,
        linked_shopify_products=db.scalar(select(func.count()).select_from(SourceProduct).where(SourceProduct.source_system_id.in_(shopify_systems))) or 0,
        linked_fos_products=db.scalar(select(func.count()).select_from(SourceProduct).where(SourceProduct.source_system_id.in_(fos_systems))) or 0,
        unresolved_links=db.scalar(select(func.count()).select_from(SourceProductLink).where(SourceProductLink.link_status == 'NEEDS_REVIEW')) or 0,
        conflicts=db.scalar(select(func.count()).select_from(SourceProductLink).where(SourceProductLink.link_status == 'CONFLICT')) or 0,
        reconciliation_ready=db.scalar(select(func.count()).select_from(InventoryReconciliationRow).where(InventoryReconciliationRow.sync_status == 'READY')) or 0,
        import_batches=db.scalar(select(func.count()).select_from(ImportBatch)) or 0,
        export_runs=db.scalar(select(func.count()).select_from(ExportRun)) or 0,
    )
