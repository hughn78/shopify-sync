from __future__ import annotations
from typing import List, Optional

from dataclasses import dataclass


@dataclass
class AIResult:
    candidate_id: Optional[int]
    score: Optional[float]
    reason: str


class LLMMatcher:
    def rank_candidates(self, source_title: str, candidates: List[dict]) -> AIResult:
        return AIResult(candidate_id=None, score=None, reason='AI disabled, using fuzzy/manual review only')