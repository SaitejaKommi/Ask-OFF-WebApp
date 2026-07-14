import duckdb
import re
import logging
import math
from typing import Iterable, Any, Optional

from adapters.base import BaseAdapter
from models.raw_product import RawProduct
from config.settings import settings

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

class OFFAdapter(BaseAdapter):
    def __init__(self, csv_path: str | None = None) -> None:
        self.csv_path = csv_path or str(settings.raw_data_path)

    def extract_raw_products(self, limit: int | None = None) -> Iterable[RawProduct]:
        con = duckdb.connect()
        try:
            from pathlib import Path
            if not Path(self.csv_path).exists():
                raise FileNotFoundError(f"Raw data CSV not found at {self.csv_path}")


            cols = [
                "code",
                "product_name",
                "brands",
                "categories",
                "ingredients_text",
                "nutriments",
                "nutriscore_grade",
                "nova_group",
                "ecoscore_grade",
                "completeness",
            ]
            cols_str = ", ".join(cols)
            
            query = f"SELECT {cols_str} FROM read_csv_auto('{self.csv_path}')"
            if limit is not None:
                query += f" LIMIT {limit}"

            res = con.execute(query)
            
            while True:
                chunk = res.fetchmany(settings.pipeline_batch_size)
                if not chunk:
                    break
                for row in chunk:
                    code = safe_str(row[0])
                    raw_product_name = safe_str(row[1])
                    raw_brands = safe_str(row[2])
                    raw_categories = safe_str(row[3])
                    raw_ingredients = safe_str(row[4])
                    raw_nutriments = safe_str(row[5])
                    
                    product_name = parse_product_name(raw_product_name)
                    if not product_name:
                        product_name = raw_product_name.strip()
                        
                    ingredients_text = parse_ingredients_text(raw_ingredients)
                    if not ingredients_text:
                        ingredients_text = raw_ingredients.strip()
                        
                    nutriments = parse_nutriments(raw_nutriments)
                    
                    yield RawProduct(
                        code=code,
                        product_name=product_name,
                        brands=raw_brands.strip(),
                        categories=raw_categories.strip(),
                        ingredients_text=ingredients_text,
                        nutriments=nutriments,
                        nutriscore_grade=safe_str(row[6]) if row[6] is not None else None,
                        nova_group=safe_int(row[7]),
                        ecoscore_grade=safe_str(row[8]) if row[8] is not None else None,
                        completeness=safe_float(row[9])
                    )
        finally:
            con.close()
