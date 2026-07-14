from retrieval.ranking import RankingManager


class TestRankingManager:
    def test_product_name_has_highest_boost(self):
        manager = RankingManager()
        boosts = manager.get_boosts()
        assert boosts["product_name"] >= boosts["brand"]
        assert boosts["product_name"] >= boosts["ingredients"]
        assert boosts["product_name"] >= boosts["category"]

    def test_brand_boost_higher_than_ingredients(self):
        manager = RankingManager()
        boosts = manager.get_boosts()
        assert boosts["brand"] >= boosts["ingredients"]

    def test_all_expected_fields_present(self):
        manager = RankingManager()
        boosts = manager.get_boosts()
        expected = [
            "product_name",
            "brand",
            "category",
            "ingredients",
            "search_text",
        ]
        for field in expected:
            assert field in boosts, f"Missing field boost: {field}"

    def test_completeness_weight_is_reasonable(self):
        manager = RankingManager()
        assert 0.0 <= manager.completeness_weight <= 1.0

