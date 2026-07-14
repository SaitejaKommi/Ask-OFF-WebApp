from typing import Optional, List, Dict, Tuple, Any
import time

from retrieval.repository import SearchRepository
from retrieval.query_parser import QueryParser
from retrieval.intent_detector import IntentDetector
from retrieval.filters import FiltersManager
from retrieval.ranking import RankingManager
from models.search_document import SearchDocument

class SearchEngine:
    def __init__(
        self, 
        repository: SearchRepository,
        ranking_manager: Optional[RankingManager] = None
    ) -> None:
        self.repository = repository
        self.ranking_manager = ranking_manager or RankingManager()

    def search(
        self,
        query: str,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        ingredients: Optional[str] = None,
        is_organic: Optional[bool] = None,
        is_vegan: Optional[bool] = None,
        is_vegetarian: Optional[bool] = None,
        size: int = 20,
        from_: int = 0
    ) -> Dict[str, Any]:
        
        start_time = time.time()
        
        parsed_query = QueryParser.parse(query)
        
        intent = IntentDetector.detect(parsed_query)
        
        search_query = parsed_query
        intent_brand = brand
        intent_category = category
        intent_ingredients = ingredients
        
        if intent["type"] == "brand":
            intent_brand = intent["extracted_term"]
            search_query = ""
        elif intent["type"] == "category":
            intent_category = intent["extracted_term"]
            search_query = ""
        elif intent["type"] == "ingredient":
            intent_ingredients = intent["extracted_term"]
            search_query = ""
            
        filters = FiltersManager.build_filters(
            brand=intent_brand,
            category=intent_category,
            ingredients=intent_ingredients,
            is_organic=is_organic,
            is_vegan=is_vegan,
            is_vegetarian=is_vegetarian
        )
        
        total, hits = self.repository.search(
            query=search_query,
            filters=filters,
            size=size,
            from_=from_
        )
        
        took_ms = int((time.time() - start_time) * 1000)
        
        return {
            "total": total,
            "hits": [
                {
                    "score": score,
                    "product": doc
                }
                for score, doc in hits
            ],
            "query": query,
            "took_ms": took_ms
        }

    def get_product(self, barcode: str) -> Optional[SearchDocument]:
        return self.repository.get_by_id(barcode)

    def autocomplete(self, query: str, size: int = 5) -> List[str]:
        parsed = QueryParser.parse(query)
        if not parsed:
            return []
        return self.repository.get_autocomplete(parsed, size=size)
