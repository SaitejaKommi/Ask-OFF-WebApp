from pydantic import BaseModel, Field
from typing import Optional


class RawProduct(BaseModel):
    code: str
    product_name: str
    brands: str
    categories: str
    ingredients_text: str
    nutriments: str
    nutriscore_grade: Optional[str] = None
    nova_group: Optional[str] = None
    ecoscore_grade: Optional[str] = None
    completeness: Optional[float] = None


class NormalizedProduct(BaseModel):
    code: str
    product_name: str
    product_name_clean: str
    brands: str
    brands_clean: str
    categories: str
    categories_clean: str
    ingredients_text: str
    ingredients_clean: str
    nutriments: dict
    nutriscore_grade: Optional[str] = None
    nova_group: Optional[int] = None
    ecoscore_grade: Optional[str] = None
    completeness: float = 0.0
    search_text: str
    semantic_document: str
