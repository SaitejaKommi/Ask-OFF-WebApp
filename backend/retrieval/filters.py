from typing import Dict, Any, Optional

class FiltersManager:
    @staticmethod
    def build_filters(
        brand: Optional[str] = None,
        category: Optional[str] = None,
        ingredients: Optional[str] = None,
        is_organic: Optional[bool] = None,
        is_vegan: Optional[bool] = None,
        is_vegetarian: Optional[bool] = None
    ) -> Dict[str, Any]:
        filters = {}
        if brand:
            filters["brand"] = brand
        if category:
            filters["category"] = category
        if ingredients:
            filters["ingredients"] = ingredients
            
        if is_organic is not None:
            filters["is_organic"] = is_organic
        if is_vegan is not None:
            filters["is_vegan"] = is_vegan
        if is_vegetarian is not None:
            filters["is_vegetarian"] = is_vegetarian
            
        return filters
