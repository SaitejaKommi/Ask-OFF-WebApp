from typing import Optional, List, Dict, Tuple, Any, Union
import time

from retrieval.repository import SearchRepository
from retrieval.query_parser import QueryParser
from retrieval.filters import FiltersManager
from models.search_document import SearchDocument
from query.search_query import SearchQuery
from query.pipeline import SearchQueryPipeline
from models.search import SearchResponse, SearchHit

class SearchEngine:
    def __init__(
        self, 
        repository: SearchRepository,
    ) -> None:
        self.repository = repository

    def search(
        self,
        query: Union[str, SearchQuery],
        filters: Optional[Dict[str, Any]] = None,
        size: int = 20,
        from_: int = 0,
        explain: bool = False
    ) -> SearchResponse:
        
        start_time = time.time()
        api_filters = filters or {}
        
        if isinstance(query, str):
            search_query = SearchQueryPipeline.process(query, size=size, from_=from_)
            
            # Merge explicit API filters into the search query
            for k, val in api_filters.items():
                if val is not None:
                    if k in ("brand", "category", "ingredients"):
                        entity_key = k + "s" if k != "ingredients" else k
                        search_query.entities.setdefault(entity_key, []).append({
                            "value": val,
                            "explanation": "Manual override from API parameter"
                        })
                    else:
                        search_query.filters[k] = val
        else:
            search_query = query
            
        # Build retrieval filters from entities and constraints
        retrieval_filters: Dict[str, Any] = {}
        
        # Only turn entities into mandatory filters if the user explicitly requested it (intent)
        # OR if it was an explicit API parameter override (in which case it was added with intent fallback)
        # We assume explicit API parameters were injected with explanation "Manual override..."
        
        def is_explicit_override(entity_list: List[Dict]) -> bool:
            if not entity_list:
                return False
            for e in entity_list:
                if "Manual override" in e.get("explanation", ""):
                    return True
            return False

        if search_query.intent == "brand_search" or is_explicit_override(search_query.entities.get("brands", [])):
            if search_query.entities.get("brands"):
                retrieval_filters["brand"] = search_query.entities["brands"][0]["value"]
                
        if search_query.intent == "category_browse" or is_explicit_override(search_query.entities.get("categories", [])):
            if search_query.entities.get("categories"):
                retrieval_filters["category"] = search_query.entities["categories"][0]["value"]
                
        if search_query.intent == "ingredient_search" or is_explicit_override(search_query.entities.get("ingredients", [])):
            if search_query.entities.get("ingredients"):
                retrieval_filters["ingredients"] = search_query.entities["ingredients"][0]["value"]
            
        # Map constraint filters to retrieval filters
        palm_oil_filter = search_query.filters.get("palm_oil")
        if palm_oil_filter is not None:
            retrieval_filters["is_palm_oil_free"] = not palm_oil_filter
            
        constraint_to_filter = {
            "organic": "is_organic",
            "vegan": "is_vegan",
            "vegetarian": "is_vegetarian",
            "high_protein": "is_high_protein",
            "low_sugar": "is_low_sugar",
            "low_sodium": "is_low_sodium",
            "gluten_free": "is_gluten_free",
            "lactose_free": "is_lactose_free",
        }
        for constraint_key, filter_key in constraint_to_filter.items():
            val = search_query.filters.get(constraint_key)
            if val is not None:
                retrieval_filters[filter_key] = val

        final_filters = FiltersManager.build_filters(retrieval_filters)
        
        text_term = search_query.text_term
        
        if search_query.intent in ("brand_search", "category_browse", "ingredient_search"):
            text_term = ""

            
        q_size = search_query.pagination.get("size", size)
        q_from = search_query.pagination.get("from", from_)
        
        total, hits, repo_metadata = self.repository.search(
            query=text_term,
            filters=final_filters,
            size=q_size,
            from_=q_from,
            explain=explain
        )
        
        took_ms = int((time.time() - start_time) * 1000)
        
        search_hits = [
            SearchHit(score=score, product=doc)
            for score, doc in hits
        ]
        
        explain_data = None
        if explain:
            explain_data = {
                "parsed_query": search_query.text_term,
                "extracted_entities": search_query.entities,
                "constraints": search_query.filters,
                "opensearch_query": repo_metadata.get("opensearch_query", {}),
                "total_results": total,
                "page": (q_from // q_size) + 1 if q_size > 0 else 1,
                "size": q_size,
            }

        return SearchResponse(
            total=total,
            hits=search_hits,
            query=query if isinstance(query, str) else query.original_query,
            took_ms=took_ms,
            search_query=explain_data
        )

    def get_product(self, barcode: str) -> Optional[SearchDocument]:
        return self.repository.get_by_id(barcode)

    def autocomplete(self, query: str, size: int = 5) -> List[str]:
        parsed = QueryParser.parse(query)
        if not parsed:
            return []
        return self.repository.get_autocomplete(parsed, size=size)
