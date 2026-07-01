import logging
from pathlib import Path
from tqdm import tqdm

from .extract import extract_required_fields
from .normalizers import (
    normalize_product_name,
    normalize_brands,
    normalize_categories,
    normalize_ingredients,
    normalize_nutriments,
    normalize_nutriscore_grade,
    normalize_nova_group,
    normalize_ecoscore_grade,
    normalize_completeness,
)
from .search_doc import build_search_text, build_semantic_document
from .load import write_normalized_parquet
from models.product import NormalizedProduct

logger = logging.getLogger(__name__)


def run_pipeline(csv_path: str | None = None) -> Path:
    logger.info("Extracting required fields from CSV...")
    df = extract_required_fields(csv_path)
    logger.info("Extracted %d rows", len(df))

    products: list[NormalizedProduct] = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Normalizing"):
        product_name, product_name_clean = normalize_product_name(row["product_name"])
        brands, brands_clean = normalize_brands(row["brands"])
        categories, categories_clean = normalize_categories(row["categories"])
        ingredients_text, ingredients_clean = normalize_ingredients(
            row["ingredients_text"]
        )

        normalized = NormalizedProduct(
            code=row["code"],
            product_name=product_name,
            product_name_clean=product_name_clean,
            brands=brands,
            brands_clean=brands_clean,
            categories=categories,
            categories_clean=categories_clean,
            ingredients_text=ingredients_text,
            ingredients_clean=ingredients_clean,
            nutriments=normalize_nutriments(row["nutriments"]),
            nutriscore_grade=normalize_nutriscore_grade(row["nutriscore_grade"]),
            nova_group=normalize_nova_group(row["nova_group"]),
            ecoscore_grade=normalize_ecoscore_grade(row["ecoscore_grade"]),
            completeness=normalize_completeness(row["completeness"]),
            search_text=build_search_text(
                product_name_clean=product_name_clean,
                brands_clean=brands_clean,
                categories_clean=categories_clean,
                ingredients_clean=ingredients_clean,
            ),
            semantic_document=build_semantic_document(
                product_name=product_name_clean,
                brands=brands_clean,
                categories=categories_clean,
                ingredients=ingredients_clean,
            ),
        )
        products.append(normalized)

    output_path = write_normalized_parquet(products)
    logger.info("Pipeline complete. Output: %s", output_path)
    return output_path
