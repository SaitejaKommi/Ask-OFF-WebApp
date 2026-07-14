from typing import Optional
from models.search_document import SearchDocument, Nutrition, NutritionItem, Flags, ProductMetadata
from models.raw_product import RawProduct

class SearchDocumentBuilder:
    @staticmethod
    def build(raw: RawProduct) -> SearchDocument:
        nutrition_dict = raw.nutriments or {}
        
        def make_item(key: str) -> Optional[NutritionItem]:
            val = nutrition_dict.get(key)
            if isinstance(val, dict):
                return NutritionItem(
                    value=val.get("value"),
                    per_100g=val.get("per_100g"),
                    unit=val.get("unit")
                )
            return None

        nutrition = Nutrition(
            energy=make_item("energy"),
            fat=make_item("fat"),
            saturates=make_item("saturates"),
            carbohydrates=make_item("carbohydrates"),
            sugars=make_item("sugars"),
            proteins=make_item("proteins"),
            salt=make_item("salt"),
            sodium=make_item("sodium")
        )
        
        core_keys = {"energy", "fat", "saturates", "carbohydrates", "sugars", "proteins", "salt", "sodium"}
        for k, v in nutrition_dict.items():
            if k not in core_keys and isinstance(v, dict):
                item = NutritionItem(
                    value=v.get("value"),
                    per_100g=v.get("per_100g"),
                    unit=v.get("unit")
                )
                nutrition.raw_nutrients[k] = item
        
        categories_lower = raw.categories.lower()
        ingredients_lower = raw.ingredients_text.lower()
        
        is_organic = (
            "organic" in categories_lower
            or "organic" in ingredients_lower
            or "bio" in categories_lower
            or "bio" in ingredients_lower
        )
        is_vegan = "vegan" in categories_lower or "vegan" in ingredients_lower
        is_vegetarian = "vegetarian" in categories_lower or "vegetarian" in ingredients_lower or is_vegan
        
        flags = Flags(
            is_organic=is_organic,
            is_vegan=is_vegan,
            is_vegetarian=is_vegetarian
        )
        
        metadata = ProductMetadata(
            nutriscore_grade=raw.nutriscore_grade,
            nova_group=raw.nova_group,
            ecoscore_grade=raw.ecoscore_grade,
            completeness=raw.completeness
        )
        
        parts = [
            p
            for p in [
                raw.product_name,
                raw.brands,
                raw.categories,
                raw.ingredients_text,
            ]
            if p
        ]
        search_text = " ".join(parts)
        
        sem_parts = []
        if raw.product_name:
            sem_parts.append(f"Product: {raw.product_name}")
        if raw.brands:
            sem_parts.append(f"Brand: {raw.brands}")
        if raw.categories:
            sem_parts.append(f"Category: {raw.categories}")
        if raw.ingredients_text:
            sem_parts.append(f"Ingredients:\n{raw.ingredients_text}")
        semantic_document = "\n\n".join(sem_parts)
        
        return SearchDocument(
            id=raw.code,
            core_product_id=None,
            variant_id=None,
            product_name=raw.product_name,
            brand=raw.brands if raw.brands else None,
            category=raw.categories if raw.categories else None,
            ingredients=raw.ingredients_text if raw.ingredients_text else None,
            nutrition=nutrition,
            flags=flags,
            metadata=metadata,
            search_text=search_text,
            semantic_document=semantic_document
        )
