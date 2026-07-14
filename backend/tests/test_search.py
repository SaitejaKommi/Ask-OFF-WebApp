from unittest.mock import MagicMock
from repositories.opensearch_repository import OpenSearchSearchRepository
from search.mappings import PRODUCT_INDEX_MAPPING
from models.search_document import SearchDocument


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
                            "nutrition": {},
                            "flags": {},
                            "metadata": {"completeness": 1.0},
                            "search_text": "honey",
                            "semantic_document": "honey",
                        },
                    }
                ],
            }
        }

        repo = OpenSearchSearchRepository(client=mock_client)
        total, hits = repo.search(
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
            "nutrition",
            "flags",
            "metadata",
            "search_text",
            "semantic_document",
        ]
        for field in required:
            assert field in props, f"Missing field: {field}"

    def test_nutrition_not_indexed(self):
        props = PRODUCT_INDEX_MAPPING["mappings"]["properties"]
        assert props["nutrition"]["enabled"] is False

