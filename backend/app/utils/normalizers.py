from __future__ import annotations

import re
import string


PUNCT_TRANSLATION = str.maketrans('', '', string.punctuation)


def normalize_whitespace(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = ' '.join(str(value).strip().split())
    return cleaned or None


def normalize_blank(value: str | None) -> str | None:
    value = normalize_whitespace(value)
    if value in {None, '', 'nan', 'NaN', 'None'}:
        return None
    return value


def normalize_identifier(value: str | int | float | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r'\d+\.0', text):
        text = text[:-2]
    return text


def normalize_name_for_match(value: str | None) -> str | None:
    value = normalize_blank(value)
    if value is None:
        return None
    lowered = value.lower().translate(PUNCT_TRANSLATION)
    lowered = re.sub(r'\s+', ' ', lowered).strip()
    return lowered or None


def normalize_location(value: str | None) -> str | None:
    value = normalize_blank(value)
    return value.lower() if value else None
