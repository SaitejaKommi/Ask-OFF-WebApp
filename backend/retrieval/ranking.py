from typing import Dict, List

from config.settings import settings


class RankingManager:
    def __init__(self) -> None:
        self.field_boosts: Dict[str, float] = {
            "product_name": 3.0,
            "brand": 2.0,
            "category": 1.5,
            "ingredients": 1.2,
            "search_text": 1.0
        }
        self.phrase_boost: float = 10.0
        self.and_match_boost: float = 5.0
        self.fuzzy_boost: float = 0.5
        self.modifier_boost: float = 2.0
        self.completeness_factor: float = getattr(settings, "completeness_weight", 0.15)

    def get_boosts(self) -> Dict[str, float]:
        return self.field_boosts

    def get_search_fields(self) -> List[str]:
        return [f"{field}^{boost}" for field, boost in self.field_boosts.items()]

