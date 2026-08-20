import pytest

from models.search_document import SearchDocument
from retrieval.search_engine import SearchEngine


class CapturingRepository:
    """Probe repository that records the filters/numeric filters it receives."""

    def __init__(self):
        self.last_filters = None
        self.last_numeric_filters = None
        self.last_text = None

    def search(self, query, filters=None, numeric_filters=None, modifiers=None,
               size=20, from_=0, explain=False):
        self.last_text = query
        self.last_filters = filters or {}
        self.last_numeric_filters = numeric_filters or []
        doc = SearchDocument(
            id="1",
            product_name="Maple Syrup",
            search_text="Maple Syrup",
            semantic_document="Maple Syrup",
        )
        return 1, [(1.0, doc)], {}

    def get_by_id(self, doc_id):
        return None

    def get_autocomplete(self, query, size=5):
        return []


@pytest.fixture
def capturing_engine():
    repo = CapturingRepository()
    return SearchEngine(repository=repo), repo


def test_category_api_filter_maps_to_categories_entity(capturing_engine):
    engine, repo = capturing_engine
    engine.search("", filters={"category": "Maple syrups"}, size=5)
    assert repo.last_filters.get("category") == "Maple syrups", (
        "Category override must become a retrieval filter "
        "(regression: 'categorys' typo previously dropped it)"
    )


def test_brand_api_filter_maps_to_brands_entity(capturing_engine):
    engine, repo = capturing_engine
    engine.search("", filters={"brand": "Kroger"}, size=5)
    assert repo.last_filters.get("brand") == "Kroger"


def test_plain_string_query_has_no_override_filters(capturing_engine):
    engine, repo = capturing_engine
    engine.search("maple syrup", size=5)
    assert repo.last_filters == {}
    assert repo.last_text != ""


def test_non_entity_api_filters_pass_through(capturing_engine):
    engine, repo = capturing_engine
    engine.search("cookies", filters={"vegan": True}, size=5)
    assert repo.last_filters.get("is_vegan") is True
