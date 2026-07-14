import json
import pandas as pd
from pathlib import Path
from models.search_document import SearchDocument
from config.settings import settings


def write_normalized_parquet(products: list[SearchDocument]) -> Path:
    records = [p.model_dump() for p in products]
    df = pd.DataFrame(records)
    for col in ["nutrition", "flags", "metadata"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x) if isinstance(x, dict) else x
            )
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = settings.processed_dir / "normalized.parquet"
    df.to_parquet(output_path, index=False, engine="pyarrow")
    return output_path


def read_normalized_parquet() -> pd.DataFrame:
    output_path = settings.processed_dir / "normalized.parquet"
    if not output_path.exists():
        raise FileNotFoundError(f"Normalized data not found at {output_path}")
    df = pd.read_parquet(output_path, engine="pyarrow")
    return df


def read_normalized_parquet_with_nutriments() -> pd.DataFrame:
    df = read_normalized_parquet()
    for col in ["nutrition", "flags", "metadata"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.loads(x) if isinstance(x, str) else x
            )
    return df

