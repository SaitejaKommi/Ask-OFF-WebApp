from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class SearchDocument(BaseModel):
    id: str
    dataset_id: str = "default"
    core_product_id: Optional[str] = None
    variant_id: Optional[str] = None
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    ingredients: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    search_text: str
    semantic_document: str
