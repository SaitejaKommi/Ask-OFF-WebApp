import duckdb
import re
import logging
import math
from typing import Iterable, Any, Optional

from adapters.base import BaseAdapter
from models.raw_product import RawProduct
from config.settings import settings

logger = logging.getLogger(__name__)

from utils.off_parser import (
    parse_product_name,
    parse_ingredients_text,
    parse_nutriments,
    safe_str,
    safe_float,
    safe_int,
)

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
