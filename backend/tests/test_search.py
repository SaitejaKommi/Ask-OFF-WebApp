from search.queries import (
    build_search_query,
    build_product_query,
    build_brand_query,
    build_category_query,
    build_autocomplete_query,
)
from search.ranking import RankingConfig
from search.mappings import PRODUCT_INDEX_MAPPING


class TestBuildSearchQuery:
    def test_returns_valid_structure(self):
        query = build_search_query("maple syrup", RankingConfig())
        assert query["size"] == 20
        assert query["from"] == 0
        assert "bool" in query["query"]
        assert "should" in query["query"]["bool"]

    def test_includes_multi_match_with_boosts(self):
        query = build_search_query("test", RankingConfig())
        should = query["query"]["bool"]["should"]
        mm = should[0]["multi_match"]
        assert "product_name_clean^3.0" in mm["fields"]
        assert "brands_clean^2.0" in mm["fields"]
        assert mm["fuzziness"] == "AUTO"

    def test_respects_size_and_offset(self):
        query = build_search_query("test", RankingConfig(), size=10, from_=5)
        assert query["size"] == 10
        assert query["from"] == 5


class TestBuildProductQuery:
    def test_uses_term_query(self):
        query = build_product_query("0008577002786")
        assert query["query"]["term"]["code"] == "0008577002786"


class TestBuildBrandQuery:
    def test_uses_match_query(self):
        query = build_brand_query("Ferrero")
        assert "match" in query["query"]
        assert query["query"]["match"]["brands_clean"]["query"] == "Ferrero"

    def test_uses_and_operator(self):
        query = build_brand_query("Butternut Mountain Farm")
        assert query["query"]["match"]["brands_clean"]["operator"] == "and"


class TestBuildCategoryQuery:
    def test_uses_match_query(self):
        query = build_category_query("Sweeteners")
        assert "match" in query["query"]
        assert query["query"]["match"]["categories_clean"]["query"] == "Sweeteners"


class TestBuildAutocompleteQuery:
    def test_uses_bool_prefix(self):
        query = build_autocomplete_query("map")
        assert query["query"]["multi_match"]["type"] == "bool_prefix"
        assert (
            "product_name_clean.autocomplete"
            in query["query"]["multi_match"]["fields"]
        )


class TestMappingStructure:
    def test_has_required_fields(self):
        props = PRODUCT_INDEX_MAPPING["mappings"]["properties"]
        required = [
            "code",
            "product_name",
            "product_name_clean",
            "brands",
            "brands_clean",
            "categories",
            "categories_clean",
            "ingredients_text",
            "ingredients_clean",
            "nutriments",
            "nutriscore_grade",
            "nova_group",
            "ecoscore_grade",
            "completeness",
            "search_text",
            "semantic_document",
        ]
        for field in required:
            assert field in props, f"Missing field: {field}"

    def test_nutriments_not_indexed(self):
        props = PRODUCT_INDEX_MAPPING["mappings"]["properties"]
        assert props["nutriments"]["enabled"] is False
