from __future__ import annotations

import pytest

from app.models import CanonicalProduct, SourceProduct, SourceSystem
from app.services.candidate_service import CandidateService


@pytest.fixture
def populated_db(db):
    system = SourceSystem(code='TEST', name='Test')
    db.add(system)
    db.flush()

    canonicals = [
        CanonicalProduct(canonical_name='Paracetamol 500mg Tablets', normalized_name='paracetamol 500mg tablets', review_status='NEEDS_REVIEW'),
        CanonicalProduct(canonical_name='Ibuprofen 200mg Capsules', normalized_name='ibuprofen 200mg capsules', review_status='NEEDS_REVIEW'),
        CanonicalProduct(canonical_name='Aspirin 300mg', normalized_name='aspirin 300mg', review_status='NEEDS_REVIEW'),
    ]
    for c in canonicals:
        db.add(c)
    db.flush()

    source = SourceProduct(
        source_system_id=system.id,
        source_record_key='test:1',
        title='Paracetamol 500mg',
        normalized_title='paracetamol 500mg',
    )
    db.add(source)
    db.flush()
    return db, source


class TestGenerateCandidates:
    def test_returns_ranked_candidates(self, populated_db):
        db, source = populated_db
        svc = CandidateService()
        candidates = svc.generate_candidates(db, 'run-1', source)
        assert len(candidates) > 0
        scores = [c.fuzzy_score for c in candidates]
        assert scores == sorted(scores, reverse=True)

    def test_top_candidate_is_paracetamol(self, populated_db):
        db, source = populated_db
        svc = CandidateService()
        candidates = svc.generate_candidates(db, 'run-2', source)
        top = candidates[0]
        canonical = db.get(CanonicalProduct, top.candidate_canonical_product_id)
        assert 'paracetamol' in canonical.normalized_name

    def test_no_title_returns_empty(self, db):
        system = SourceSystem(code='T2', name='T2')
        db.add(system)
        db.flush()
        source = SourceProduct(
            source_system_id=system.id,
            source_record_key='t:1',
            title='Unknown',
            normalized_title=None,
        )
        db.add(source)
        db.flush()
        svc = CandidateService()
        result = svc.generate_candidates(db, 'run-3', source)
        assert result == []

    def test_respects_limit(self, populated_db):
        db, source = populated_db
        svc = CandidateService()
        candidates = svc.generate_candidates(db, 'run-4', source, limit=1)
        assert len(candidates) <= 1
