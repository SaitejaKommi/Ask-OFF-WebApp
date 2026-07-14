from typing import Dict

class RankingManager:
    def __init__(self) -> None:
        self.field_boosts = {
            "product_name": 3.0,
            "brand": 2.0,
            "category": 1.5,
            "ingredients": 1.2,
            "search_text": 1.0
        }
        self.completeness_weight = 0.15

    def get_boosts(self) -> Dict[str, float]:
        return self.field_boosts
