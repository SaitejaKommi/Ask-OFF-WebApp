import ast
import math
import logging

logger = logging.getLogger(__name__)


def parse_multilingual_field(raw: str) -> list[dict[str, str]]:
    if not raw or raw == "[]":
        return []
    normalized = raw.replace("}\n {", "}, {")
    try:
        result = ast.literal_eval(normalized)
        if isinstance(result, list):
            return result
        return []
    except (SyntaxError, ValueError, TypeError) as exc:
        logger.warning("Failed to parse multilingual field: %s", exc)
        return []


def extract_text_by_language(
    entries: list[dict[str, str]],
    preferred_langs: tuple[str, ...] = ("en", "main", "fr"),
) -> str:
    if not entries:
        return ""
    for entry in entries:
        if isinstance(entry, dict) and entry.get("lang") in preferred_langs:
            text = entry.get("text", "")
            if text:
                return text
    for entry in entries:
        if isinstance(entry, dict):
            text = entry.get("text", "")
            if text:
                return text
    return ""


def parse_product_name(raw: str) -> str:
    entries = parse_multilingual_field(raw)
    return extract_text_by_language(entries)


def parse_ingredients_text(raw: str) -> str:
    entries = parse_multilingual_field(raw)
    return extract_text_by_language(entries)


def _sanitize(val: object) -> object:
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def parse_nutriments(raw: str) -> dict[str, dict]:
    entries = parse_multilingual_field(raw)
    result: dict[str, dict] = {}
    for entry in entries:
        if isinstance(entry, dict):
            name = entry.get("name", "")
            if name:
                result[name] = {
                    "value": _sanitize(entry.get("value")),
                    "per_100g": _sanitize(entry.get("100g")),
                    "unit": _sanitize(entry.get("unit")),
                }
    return result
