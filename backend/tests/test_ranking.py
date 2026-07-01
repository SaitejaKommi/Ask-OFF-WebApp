from search.ranking import RankingConfig


class TestRankingConfig:
    def test_product_name_has_highest_boost(self):
        config = RankingConfig()
        assert config.field_boosts["product_name_clean"] >= config.field_boosts["brands_clean"]
        assert config.field_boosts["product_name_clean"] >= config.field_boosts["ingredients_clean"]
        assert config.field_boosts["product_name_clean"] >= config.field_boosts["categories_clean"]

    def test_brand_boost_higher_than_ingredients(self):
        config = RankingConfig()
        assert config.field_boosts["brands_clean"] >= config.field_boosts["ingredients_clean"]

    def test_all_expected_fields_present(self):
        config = RankingConfig()
        expected = [
            "product_name_clean",
            "product_name",
            "brands_clean",
            "brands",
            "search_text",
            "ingredients_clean",
            "ingredients_text",
            "categories_clean",
            "categories",
        ]
        for field in expected:
            assert field in config.field_boosts, f"Missing field boost: {field}"

    def test_completeness_weight_is_reasonable(self):
        config = RankingConfig()
        assert 0.0 <= config.completeness_weight <= 1.0
