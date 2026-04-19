from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AIResult:
    candidate_id: int | None
    score: float | None
    reason: str


class LLMMatcher:
    def rank_candidates(self, source_title: str, candidates: list[dict]) -> AIResult:
        return AIResult(candidate_id=None, score=None, reason='AI disabled, using fuzzy/manual review only')
