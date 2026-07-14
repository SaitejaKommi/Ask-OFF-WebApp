from retrieval.repository import SearchRepository
from repositories.opensearch_repository import OpenSearchSearchRepository
from retrieval.search_engine import SearchEngine

_search_repository: SearchRepository | None = None
_search_engine: SearchEngine | None = None


def get_search_repository() -> SearchRepository:
    global _search_repository
    if _search_repository is None:
        _search_repository = OpenSearchSearchRepository()
    return _search_repository


def get_search_engine() -> SearchEngine:
    global _search_engine
    if _search_engine is None:
        repository = get_search_repository()
        _search_engine = SearchEngine(repository)
    return _search_engine

