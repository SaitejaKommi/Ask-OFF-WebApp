from pipeline.normalizers import (
    normalize_product_name,
    normalize_brands,
    normalize_categories,
    normalize_ingredients,
    normalize_nutriments,
    normalize_nutriscore_grade,
    normalize_nova_group,
    normalize_ecoscore_grade,
    normalize_completeness,
)


class TestNormalizeProductName:
    def test_parses_multilingual_field(self, sample_raw_product_name):
        original, cleaned = normalize_product_name(sample_raw_product_name)
        assert original == "Organic Vermont Maple Syrup"
        assert cleaned == "Organic Vermont Maple Syrup"

    def test_handles_empty_string(self):
        original, cleaned = normalize_product_name("")
        assert original == ""
        assert cleaned == ""

    def test_handles_empty_list(self):
        original, cleaned = normalize_product_name("[]")
        assert original == ""
        assert cleaned == ""

    def test_handles_plain_text(self):
        original, cleaned = normalize_product_name("Nutella")
        assert original == "Nutella"
        assert cleaned == "Nutella"


class TestNormalizeBrands:
    def test_preserves_brand_text(self):
        original, cleaned = normalize_brands("Ferrero")
        assert original == "Ferrero"
        assert cleaned == "Ferrero"

    def test_trims_whitespace(self):
        original, cleaned = normalize_brands("  Ferrero  ")
        assert cleaned == "Ferrero"

    def test_handles_empty(self):
        original, cleaned = normalize_brands("")
        assert original == ""
        assert cleaned == ""


class TestNormalizeCategories:
    def test_preserves_categories(self):
        original, cleaned = normalize_categories("Sweeteners,Syrups")
        assert cleaned == "Sweeteners,Syrups"

    def test_trims_whitespace(self):
        original, cleaned = normalize_categories("  Sweeteners , Syrups  ")
        assert cleaned == "Sweeteners , Syrups"


class TestNormalizeIngredients:
    def test_parses_multilingual_field(self, sample_raw_ingredients):
        original, cleaned = normalize_ingredients(sample_raw_ingredients)
        assert original == "Pure organic maple syrup"
        assert cleaned == "Pure organic maple syrup"

    def test_handles_empty_list(self):
        original, cleaned = normalize_ingredients("[]")
        assert original == ""
        assert cleaned == ""

    def test_handles_plain_text(self):
        original, cleaned = normalize_ingredients("water, sugar, cocoa")
        assert original == "water, sugar, cocoa"
        assert cleaned == "water, sugar, cocoa"


class TestNormalizeNutriments:
    def test_parses_nutriments(self, sample_raw_nutriments):
        result = normalize_nutriments(sample_raw_nutriments)
        assert "energy" in result
        assert result["energy"]["value"] == 333.0
        assert result["energy"]["per_100g"] == 1393.0
        assert result["energy"]["unit"] == "kcal"

    def test_handles_empty(self):
        assert normalize_nutriments("") == {}

    def test_handles_empty_list(self):
        assert normalize_nutriments("[]") == {}


class TestNormalizeNutriscoreGrade:
    def test_normalizes_valid_grade(self):
        assert normalize_nutriscore_grade("e") == "e"
        assert normalize_nutriscore_grade("E") == "e"
        assert normalize_nutriscore_grade("a") == "a"

    def test_returns_none_for_unknown(self):
        assert normalize_nutriscore_grade("unknown") is None
        assert normalize_nutriscore_grade("not-applicable") is None

    def test_returns_none_for_empty(self):
        assert normalize_nutriscore_grade("") is None
        assert normalize_nutriscore_grade(None) is None  # type: ignore


class TestNormalizeNovaGroup:
    def test_normalizes_valid_group(self):
        assert normalize_nova_group("1.0") == 1
        assert normalize_nova_group("2") == 2
        assert normalize_nova_group("4.0") == 4

    def test_returns_none_for_empty(self):
        assert normalize_nova_group("") is None

    def test_returns_none_for_invalid(self):
        assert normalize_nova_group("invalid") is None


class TestNormalizeEcoscoreGrade:
    def test_normalizes_valid_grade(self):
        assert normalize_ecoscore_grade("b") == "b"
        assert normalize_ecoscore_grade("a-plus") == "a-plus"

    def test_returns_none_for_unknown(self):
        assert normalize_ecoscore_grade("unknown") is None

    def test_returns_none_for_empty(self):
        assert normalize_ecoscore_grade("") is None


class TestNormalizeCompleteness:
    def test_normalizes_valid_value(self):
        assert normalize_completeness("0.6625") == 0.6625
        assert normalize_completeness("1.0") == 1.0
        assert normalize_completeness("0.0") == 0.0

    def test_clamps_values(self):
        assert normalize_completeness("1.5") == 1.0
        assert normalize_completeness("-0.5") == 0.0

    def test_returns_zero_for_invalid(self):
        assert normalize_completeness("") == 0.0
        assert normalize_completeness("abc") == 0.0
