import math
from typing import Any

from utils.off_parser import parse_product_name, parse_ingredients_text, parse_nutriments
from utils.text_utils import clean_text, safe_strip, safe_str


def normalize_product_name(raw: Any) -> tuple[str, str]:
    raw_str = safe_str(raw)
    if not raw_str or raw_str == "[]":
        return "", ""
    text = parse_product_name(raw_str)
    if not text:
        text = safe_strip(raw_str)
    cleaned = clean_text(text)
    return text, cleaned


def normalize_brands(raw: Any) -> tuple[str, str]:
    raw_str = safe_str(raw)
    cleaned = clean_text(safe_strip(raw_str))
    return raw_str, cleaned


def normalize_categories(raw: Any) -> tuple[str, str]:
    raw_str = safe_str(raw)
    cleaned = clean_text(safe_strip(raw_str))
    return raw_str, cleaned


def normalize_ingredients(raw: Any) -> tuple[str, str]:
    raw_str = safe_str(raw)
    if not raw_str or raw_str == "[]":
        return "", ""
    text = parse_ingredients_text(raw_str)
    if not text:
        text = safe_strip(raw_str)
    cleaned = clean_text(text)
    return text, cleaned


def normalize_nutriments(raw: Any) -> dict:
    return parse_nutriments(safe_str(raw))


def normalize_nutriscore_grade(raw: Any) -> str | None:
    val = safe_strip(raw)
    if not val or val.lower() in ("unknown", "not-applicable", "none", ""):
        return None
    return val.lower()


def normalize_nova_group(raw: Any) -> int | None:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return None
    if isinstance(raw, (int, float)):
        return int(raw)
    val = safe_strip(raw)
    if not val:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def normalize_ecoscore_grade(raw: Any) -> str | None:
    val = safe_strip(raw)
    if not val or val.lower() in ("unknown", "not-applicable", "none", ""):
        return None
    return val.lower()


def normalize_completeness(raw: Any) -> float:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return 0.0
    try:
        val = float(raw)
        return max(0.0, min(val, 1.0))
    except (ValueError, TypeError):
        return 0.0
