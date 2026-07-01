from search.client import get_client
from search.queries import (
    build_search_query,
    build_product_query,
    build_brand_query,
    build_category_query,
    build_autocomplete_query,
)
from search.ranking import RankingConfig
from models.search import SearchResponse, SearchHit, ProductResponse
from config.settings import settings


class SearchService:
    def __init__(self) -> None:
        self.client = get_client()
        self.index = settings.opensearch_index
        self.ranking_config = RankingConfig()

    def search(self, q: str, size: int = 20, from_: int = 0) -> SearchResponse:
        query = build_search_query(q, self.ranking_config, size=size, from_=from_)
        response = self.client.search(index=self.index, body=query)
        return self._build_response(response, q)

    def get_product(self, code: str) -> ProductResponse | None:
        query = build_product_query(code)
        response = self.client.search(index=self.index, body=query)
        hits = response["hits"]["hits"]
        if not hits:
            return None
        return ProductResponse(**hits[0]["_source"])

    def search_by_brand(self, brand: str, size: int = 20) -> SearchResponse:
        query = build_brand_query(brand, size=size)
        response = self.client.search(index=self.index, body=query)
        return self._build_response(response, brand)

    def search_by_category(self, category: str, size: int = 20) -> SearchResponse:
        query = build_category_query(category, size=size)
        response = self.client.search(index=self.index, body=query)
        return self._build_response(response, category)

    def autocomplete(self, q: str, size: int = 5) -> list[str]:
        query = build_autocomplete_query(q, size=size)
        response = self.client.search(index=self.index, body=query)
        hits = response["hits"]["hits"]
        return [h["_source"].get("product_name_clean", "") for h in hits]

    def _build_response(self, response: dict, query: str) -> SearchResponse:
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        took_ms = response.get("took", 0)

        search_hits = [
            SearchHit(score=h["_score"], product=ProductResponse(**h["_source"]))
            for h in hits
        ]

        return SearchResponse(
            total=total,
            hits=search_hits,
            query=query,
            took_ms=took_ms,
        )
