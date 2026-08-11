import re
import logging
import math
from typing import Any, Optional

logger = logging.getLogger(__name__)


def parse_multilingual_field(raw: str) -> list[dict[str, str]]:
    if not raw or raw == "[]":
        return []
    
    blocks = re.findall(r'\{([^{}]+)\}', raw)
    results = []
    for block in blocks:
        lang_match = re.search(r"['\"]lang['\"]\s*:\s*['\"]([^'\"]*)['\"]", block)
        text_match = re.search(r"['\"]text['\"]\s*:\s*(['\"])(.*?)\1\s*(?:,|$)", block, re.DOTALL)
        if not text_match:
            text_match = re.search(r"['\"]text['\"]\s*:\s*'(.*)'\s*$", block, re.DOTALL)
            if not text_match:
                text_match = re.search(r"['\"]text['\"]\s*:\s*\"(.*)\"\s*$", block, re.DOTALL)
        
        if lang_match and text_match:
            results.append({
                "lang": lang_match.group(1),
                "text": text_match.group(2).strip()
            })
    return results


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


def parse_nutriments(raw: str) -> dict[str, dict]:
    if not raw or raw == "[]":
        return {}
    
    blocks = re.findall(r'\{([^{}]+)\}', raw)
    result = {}
    for block in blocks:
        name_match = re.search(r"['\"]name['\"]\s*:\s*['\"]([^'\"]*)['\"]", block)
        if not name_match:
            continue
        name = name_match.group(1)
        
        value_match = re.search(r"['\"]value['\"]\s*:\s*([^\s,}]+)", block)
        value = None
        if value_match:
            val_str = value_match.group(1).strip("'\"")
            if val_str.lower() not in ('nan', 'none', 'null'):
                try:
                    value = float(val_str)
                except ValueError:
                    pass
        
        per_100g_match = re.search(r"['\"]100g['\"]\s*:\s*([^\s,}]+)", block)
        per_100g = None
        if per_100g_match:
            val_str = per_100g_match.group(1).strip("'\"")
            if val_str.lower() not in ('nan', 'none', 'null'):
                try:
                    per_100g = float(val_str)
                except ValueError:
                    pass
        
        unit_match = re.search(r"['\"]unit['\"]\s*:\s*['\"]([^'\"]*)['\"]", block)
        unit = None
        if unit_match:
            unit = unit_match.group(1)
            
        result[name] = {
            "value": value,
            "per_100g": per_100g,
            "unit": unit
        }
    return result

def safe_str(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, float) and math.isnan(val):
        return ""
    return str(val)

def safe_float(val: Any) -> float:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def safe_int(val: Any) -> Optional[int]:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None
