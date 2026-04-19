from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ExportRun, ImportBatch, ManualReviewAction


class AuditService:
    def summary(self, db: Session) -> dict:
        return {
            'imports': db.scalar(select(func.count()).select_from(ImportBatch)) or 0,
            'exports': db.scalar(select(func.count()).select_from(ExportRun)) or 0,
            'manual_actions': db.scalar(select(func.count()).select_from(ManualReviewAction)) or 0,
        }
