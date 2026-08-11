from pydantic import BaseModel
from typing import List, Optional
from models.search_document import SearchDocument


class SearchHit(BaseModel):
    score: float
    product: SearchDocument


class SearchResponse(BaseModel):
    total: int
    hits: List[SearchHit]
    query: str
    took_ms: int
    search_query: Optional[dict] = None
