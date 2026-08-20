from pathlib import Path

import duckdb
import pandas as pd

from config.settings import settings

REQUIRED_COLUMNS = [
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


def extract_required_fields(csv_path: str | None = None) -> pd.DataFrame:
    path = Path(csv_path or settings.raw_data_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw data CSV not found at {path}")

    con = duckdb.connect()
    try:
        cols = ", ".join(REQUIRED_COLUMNS)
        query = f"SELECT {cols} FROM read_csv_auto('{path}')"
        df = con.execute(query).fetchdf()
        return df
    finally:
        con.close()
