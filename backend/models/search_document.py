from pydantic import BaseModel, Field
from typing import Optional, Dict

class NutritionItem(BaseModel):
    value: Optional[float] = None
    per_100g: Optional[float] = None
    unit: Optional[str] = None

class Nutrition(BaseModel):
    energy: Optional[NutritionItem] = None
    fat: Optional[NutritionItem] = None
    saturates: Optional[NutritionItem] = None
    carbohydrates: Optional[NutritionItem] = None
    sugars: Optional[NutritionItem] = None
    proteins: Optional[NutritionItem] = None
    salt: Optional[NutritionItem] = None
    sodium: Optional[NutritionItem] = None
    raw_nutrients: Dict[str, NutritionItem] = Field(default_factory=dict)

class Flags(BaseModel):
    is_organic: bool = False
    is_vegan: bool = False
    is_vegetarian: bool = False

class ProductMetadata(BaseModel):
    nutriscore_grade: Optional[str] = None
    nova_group: Optional[int] = None
    ecoscore_grade: Optional[str] = None
    completeness: float = 0.0

class SearchDocument(BaseModel):
    id: str
    core_product_id: Optional[str] = None
    variant_id: Optional[str] = None
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    ingredients: Optional[str] = None
    nutrition: Nutrition
    flags: Flags
    metadata: ProductMetadata
    search_text: str
    semantic_document: str
