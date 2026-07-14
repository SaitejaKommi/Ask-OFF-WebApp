from typing import Optional, Tuple, List
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError

from models.search_document import SearchDocument
from retrieval.repository import SearchRepository
from config.settings import settings
from search.client import get_client

class OpenSearchSearchRepository(SearchRepository):
    def __init__(self, client: Optional[OpenSearch] = None) -> None:
        self.client = client or get_client()
        self.index = settings.opensearch_index

    def search(
        self, 
        query: str, 
        filters: Optional[dict] = None, 
        size: int = 20, 
        from_: int = 0
    ) -> Tuple[int, List[Tuple[float, SearchDocument]]]:
        
        must_clauses = []
        should_clauses = []
        
        fields = [
            "product_name^3.0",
            "brand^2.0",
            "category^1.5",
            "ingredients^1.2",
            "search_text^1.0"
        ]
        
        if query and query != "*":
            should_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": fields,
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "operator": "or",
                }
            })
        elif query == "*":
            must_clauses.append({"match_all": {}})
        
        if filters:
            for k, v in filters.items():
                if k == "brand" and v:
                    must_clauses.append({"match": {"brand": {"query": v, "operator": "and"}}})
                elif k == "category" and v:
                    must_clauses.append({"match": {"category": {"query": v, "operator": "and"}}})
                elif k == "ingredients" and v:
                    must_clauses.append({"match": {"ingredients": {"query": v, "operator": "and"}}})
        
        if not must_clauses and not should_clauses:
            must_clauses.append({"match_all": {}})

        bool_query = {
            "bool": {
                "must": must_clauses,
                "should": should_clauses,
                "minimum_should_match": 1 if (should_clauses and not must_clauses) else 0
            }
        }

        
        query_body = {
            "size": size,
            "from": from_,
            "query": {
                "function_score": {
                    "query": bool_query,
                    "functions": [
                        {
                            "field_value_factor": {
                                "field": "metadata.completeness",
                                "factor": 0.15,
                                "missing": 0.0
                            }
                        }
                    ],
                    "boost_mode": "sum"
                }
            }
        }
        
        response = self.client.search(index=self.index, body=query_body)
        
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        
        results = []
        for h in hits:
            score = h["_score"]
            doc = SearchDocument(**h["_source"])
            results.append((score, doc))
            
        return total, results

    def get_by_id(self, doc_id: str) -> Optional[SearchDocument]:
        try:
            response = self.client.get(index=self.index, id=doc_id)
            return SearchDocument(**response["_source"])
        except NotFoundError:
            # Fallback search for documents that might match 'id' field
            query_body = {
                "query": {
                    "term": {
                        "id": doc_id
                    }
                }
            }
            res = self.client.search(index=self.index, body=query_body)
            hits = res["hits"]["hits"]
            if hits:
                return SearchDocument(**hits[0]["_source"])
            return None

    def get_autocomplete(self, query: str, size: int = 5) -> List[str]:
        query_body = {
            "size": size,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "product_name.autocomplete",
                        "search_text.autocomplete",
                    ],
                    "type": "bool_prefix",
                }
            },
        }
        response = self.client.search(index=self.index, body=query_body)
        hits = response["hits"]["hits"]
        return [h["_source"].get("product_name", "") for h in hits]
