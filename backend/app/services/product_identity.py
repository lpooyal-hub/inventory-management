from __future__ import annotations

import re
from dataclasses import dataclass


CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9-]*$")


@dataclass
class ParsedProductIdentity:
    product_code: str | None
    legacy_code: str | None
    name: str


def parse_product_identity(
    product_code: str | None,
    legacy_code: str | None,
    name: str,
) -> ParsedProductIdentity:
    normalized_product_code = _clean_value(product_code)
    normalized_legacy_code = _clean_value(legacy_code)
    normalized_name = (name or "").strip()

    if " / " in normalized_name:
        prefix, suffix = normalized_name.split(" / ", 1)
        candidate_code = _clean_value(prefix)
        if candidate_code and _looks_like_code(candidate_code) and suffix.strip():
            normalized_name = suffix.strip()
            if not normalized_legacy_code:
                normalized_legacy_code = candidate_code

    return ParsedProductIdentity(
        product_code=normalized_product_code,
        legacy_code=normalized_legacy_code,
        name=normalized_name,
    )


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _looks_like_code(value: str) -> bool:
    return bool(CODE_PATTERN.fullmatch(value.upper()))
