from __future__ import annotations
from typing import List

def build_match_prompt(source_title: str, candidates: List[dict]) -> str:
    return (
        'You are assisting pharmacy product identity resolution. '
        'Be strict about pack size, strength, flavour, and formulation. '
        'Return JSON only with candidate_id, score, and reason. '
        f'Source: {source_title}. Candidates: {candidates}'
    )