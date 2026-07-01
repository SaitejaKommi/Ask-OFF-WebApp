def build_search_text(
    product_name_clean: str,
    brands_clean: str,
    categories_clean: str,
    ingredients_clean: str,
) -> str:
    parts = [
        p
        for p in [
            product_name_clean,
            brands_clean,
            categories_clean,
            ingredients_clean,
        ]
        if p
    ]
    return " ".join(parts)


def build_semantic_document(
    product_name: str,
    brands: str,
    categories: str,
    ingredients: str,
) -> str:
    parts = []
    if product_name:
        parts.append(f"Product: {product_name}")
    if brands:
        parts.append(f"Brand: {brands}")
    if categories:
        parts.append(f"Category: {categories}")
    if ingredients:
        parts.append(f"Ingredients:\n{ingredients}")
    return "\n\n".join(parts)
