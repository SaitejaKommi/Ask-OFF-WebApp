from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class SearchQuery(BaseModel):
    original_query: str
    normalized_query: str
    text_term: str = ""
    intent: str = "generic_search"
    entities: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    
    filters: Dict[str, Any] = Field(default_factory=dict)
    
    ranking_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    pagination: Dict[str, int] = Field(default_factory=lambda: {
        "size": 20,
        "from": 0
    })
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
