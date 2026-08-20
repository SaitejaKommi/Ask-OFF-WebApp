from unittest.mock import MagicMock

from models.search_document import SearchDocument
from repositories.opensearch_repository import OpenSearchSearchRepository
from search.mappings import PRODUCT_INDEX_MAPPING


class TestOpenSearchSearchRepository:
    def test_search_constructs_valid_opensearch_dsl(self):
        mock_client = MagicMock()
        # Mock the search response format
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_score": 1.5,
                        "_source": {
                            "id": "100",
                            "product_name": "Organic Honey",
                            "brand": "Bee",
                            "category": "Sweeteners",
                            "ingredients": "Honey",
                            "attributes": {},
                            "metadata": {"completeness": 1.0},
                            "search_text": "honey",
                            "semantic_document": "honey",
                        },
                    }
                ],
            }
        }

        repo = OpenSearchSearchRepository(client=mock_client)
        total, hits, _ = repo.search(
            query="honey",
            filters={"brand": "Bee"},
            size=10,
            from_=0,
        )

        assert total == 1
        assert len(hits) == 1
        score, doc = hits[0]
        assert score == 1.5
        assert isinstance(doc, SearchDocument)
        assert doc.id == "100"
        assert doc.product_name == "Organic Honey"

        # Assert search body DSL was built correctly
        body_passed = mock_client.search.call_args[1]["body"]
        assert body_passed["size"] == 10
        assert body_passed["from"] == 0
        # Check that brand filter was appended
        must_clause = body_passed["query"]["function_score"]["query"]["bool"]["must"]
        assert must_clause[0]["match"]["brand"]["query"] == "Bee"

    def test_search_enforces_minimum_should_match_with_filters(self):
        mock_client = MagicMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        repo = OpenSearchSearchRepository(client=mock_client)

        repo.search(query="honey", filters={"is_organic": True})

        body_passed = mock_client.search.call_args[1]["body"]
        bool_query = body_passed["query"]["function_score"]["query"]["bool"]

        # Should have a should clause (for text search)
        assert len(bool_query["should"]) == 1
        # Should have a must clause (for organic filter)
        assert len(bool_query["must"]) == 1
        # Crucial bugfix: minimum_should_match MUST be 1 so the text search is mandatory
        assert bool_query["minimum_should_match"] == 1


class TestMappingStructure:
    def test_has_required_fields(self):
        props = PRODUCT_INDEX_MAPPING["mappings"]["properties"]
        required = [
            "id",
            "core_product_id",
            "variant_id",
            "product_name",
            "brand",
            "category",
            "ingredients",
            "attributes",
            "metadata",
            "search_text",
            "semantic_document",
        ]
        for field in required:
            assert field in props, f"Missing field: {field}"

    def test_attributes_indexed_dynamically(self):
        props = PRODUCT_INDEX_MAPPING["mappings"]["properties"]
        assert props["attributes"]["dynamic"] is True

