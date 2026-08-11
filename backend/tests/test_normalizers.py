from adapters.off_adapter import (
    parse_product_name,
    parse_ingredients_text,
    parse_nutriments,
    safe_str,
    safe_float,
    safe_int,
)
from models.raw_product import RawProduct
from builders.search_document_builder import SearchDocumentBuilder


class TestOFFAdapterParsing:
    def test_parses_multilingual_name_with_escaped_quotes(self, sample_raw_product_name):
        text = parse_product_name(sample_raw_product_name)
        assert text == "Organic Vermont Maple Syrup"

    def test_parses_multilingual_ingredients(self, sample_raw_ingredients):
        text = parse_ingredients_text(sample_raw_ingredients)
        assert text == "Pure organic maple syrup"

    def test_parses_nutriments_with_values(self, sample_raw_nutriments):
        result = parse_nutriments(sample_raw_nutriments)
        assert "energy" in result
        assert result["energy"]["value"] == 333.0
        assert result["energy"]["per_100g"] == 1393.0
        assert result["energy"]["unit"] == "kcal"

    def test_handles_empty_fields(self):
        assert parse_product_name("") == ""
        assert parse_ingredients_text("[]") == ""
        assert parse_nutriments("") == {}


class TestSearchDocumentBuilder:
    def test_builder_maps_fields_and_computes_flags(self):
        raw = RawProduct(
            code="12345",
            product_name="Bio Organic Granola",
            brands="Whole Foods",
            categories="Breakfast cereals, Granola",
            ingredients_text="Organic rolled oats, organic sugar, almonds, vegan cocoa",
            nutriments={
                "energy": {"value": 450.0, "per_100g": 450.0, "unit": "kcal"},
                "fat": {"value": 15.0, "per_100g": 15.0, "unit": "g"},
            },
            nutriscore_grade="a",
            nova_group=3,
            ecoscore_grade="b",
            completeness=0.88,
        )

        doc = SearchDocumentBuilder.build(raw)

        # Basic properties
        assert doc.id == "12345"
        assert doc.product_name == "Bio Organic Granola"
        assert doc.brand == "Whole Foods"
        assert doc.category == "Breakfast cereals, Granola"
        assert doc.ingredients == "Organic rolled oats, organic sugar, almonds, vegan cocoa"

        # Nutrition dict
        assert doc.attributes["nutrition"]["energy"]["value"] == 450.0
        assert doc.attributes["nutrition"]["fat"]["value"] == 15.0
        assert "saturates" not in doc.attributes["nutrition"]

        # Flags auto-derived by builder
        assert doc.attributes["flags"]["is_organic"] is True
        assert doc.attributes["flags"]["is_vegan"] is True
        assert doc.attributes["flags"]["is_vegetarian"] is True

        # Metadata map
        assert doc.metadata["nutriscore_grade"] == "a"
        assert doc.metadata["nova_group"] == 3
        assert doc.metadata["completeness"] == 0.88

        # Text concatenation
        assert "Bio Organic Granola" in doc.search_text
        assert "Whole Foods" in doc.search_text
        assert "Ingredients:\nOrganic rolled oats" in doc.semantic_document

