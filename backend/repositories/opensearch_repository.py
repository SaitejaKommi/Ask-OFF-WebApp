from typing import List, Optional, Tuple

from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError

from config.settings import settings
from models.search_document import SearchDocument
from retrieval.ranking import RankingManager
from retrieval.repository import SearchRepository
from search.client import get_client

NUTRIENT_FIELD_MAP = {
    "protein": "proteins",
    "proteins": "proteins",
    "sugar": "sugars",
    "sugars": "sugars",
    "fat": "fat",
    "calories": "energy-kcal",
    "kcal": "energy-kcal",
    "energy": "energy-kcal",
    "sodium": "sodium",
    "salt": "salt",
    "carbs": "carbohydrates",
    "carbohydrates": "carbohydrates",
    "fiber": "fiber",
    "saturated fat": "saturated-fat",
}

class OpenSearchSearchRepository(SearchRepository):
    def __init__(self, client: Optional[OpenSearch] = None, ranking_manager: Optional[RankingManager] = None) -> None:
        self.client = client or get_client()
        self.index = settings.opensearch_index
        self.ranking_manager = ranking_manager or RankingManager()

    def search(
        self,
        query: str,
        filters: Optional[dict] = None,
        numeric_filters: Optional[List[dict]] = None,
        modifiers: Optional[List[str]] = None,
        size: int = 20,
        from_: int = 0,
        explain: bool = False
    ) -> Tuple[int, List[Tuple[float, SearchDocument]], dict]:

        must_clauses = []
        should_clauses = []
        must_not_clauses = []

        fields = self.ranking_manager.get_search_fields()

        if query and query != "*":
            should_clauses.append({
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": fields,
                                "type": "phrase",
                                "boost": self.ranking_manager.phrase_boost
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "fields": fields,
                                "operator": "and",
                                "boost": self.ranking_manager.and_match_boost
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "fields": fields,
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "operator": "or",
                                "boost": self.ranking_manager.fuzzy_boost
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            })
        elif query == "*":
            must_clauses.append({"match_all": {}})

        if modifiers:
            # Boost for modifiers like fresh, frozen, raw, salted
            for mod in modifiers:
                should_clauses.append({
                    "match": {
                        "product_name": {
                            "query": mod,
                            "boost": self.ranking_manager.modifier_boost
                        }
                    }
                })

        if filters:
            for k, v in filters.items():
                if k == "brand" and v:
                    must_clauses.append({"match": {"brand": {"query": v, "operator": "and"}}})
                elif k == "category" and v:
                    must_clauses.append({"match": {"category": {"query": v, "operator": "and"}}})
                elif k == "ingredients" and v:
                    must_clauses.append({"match": {"ingredients": {"query": v, "operator": "and"}}})
                elif k == "is_palm_oil_free":
                    if v is True:
                        # Robust negation for palm oil
                        should_clauses.append({"term": {"attributes.flags.is_palm_oil_free": {"value": True, "boost": 2.0}}})
                        must_not_clauses.append({"match": {"ingredients": "palm oil"}})
                    elif v is False:
                        # Must contain palm oil
                        must_clauses.append({"match": {"ingredients": "palm oil"}})
                elif k.startswith("is_") and v is not None:
                    # For other boolean constraints, we keep them as must for now,
                    # but they could also be softened.
                    must_clauses.append({"term": {f"attributes.flags.{k}": v}})

        if numeric_filters:
            for nf in numeric_filters:
                nutrient = nf.get("nutrient")
                op = nf.get("operator")
                val = nf.get("value")
                basis = nf.get("comparison_basis", "per_100g")

                mapped_nutrient = NUTRIENT_FIELD_MAP.get(nutrient, nutrient)

                field_path = f"attributes.nutrition.{mapped_nutrient}.{basis}"
                must_clauses.append({
                    "range": {
                        field_path: {
                            op: val
                        }
                    }
                })

        if not must_clauses and not should_clauses:
            must_clauses.append({"match_all": {}})

        bool_query = {
            "bool": {
                "must": must_clauses,
                "should": should_clauses,
                "must_not": must_not_clauses,
                "minimum_should_match": 1 if (query and query != "*") else 0
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
                                "factor": self.ranking_manager.completeness_factor,
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

        metadata = {}
        if explain:
            metadata["opensearch_query"] = query_body

        return total, results, metadata

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
