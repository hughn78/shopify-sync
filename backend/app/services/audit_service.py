from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ExportRun, ImportBatch, ManualReviewAction
from app.services.source_identity_service import SourceIdentityService


class AuditService:
    def summary(self, db: Session) -> dict:
        source_identity_service = SourceIdentityService()
        duplicate_preview = source_identity_service.preview_backfill(db)
        return {
            'imports': db.scalar(select(func.count()).select_from(ImportBatch)) or 0,
            'exports': db.scalar(select(func.count()).select_from(ExportRun)) or 0,
            'manual_actions': db.scalar(select(func.count()).select_from(ManualReviewAction)) or 0,
            'legacy_duplicate_groups': duplicate_preview['group_count'],
            'legacy_duplicate_records': duplicate_preview['duplicate_count'],
        }
