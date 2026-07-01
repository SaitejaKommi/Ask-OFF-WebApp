from dataclasses import dataclass, field


@dataclass(frozen=True)
class RankingConfig:
    field_boosts: dict[str, float] = field(
        default_factory=lambda: {
            "product_name_clean": 3.0,
            "product_name": 2.5,
            "brands_clean": 2.0,
            "brands": 1.5,
            "search_text": 1.8,
            "ingredients_clean": 1.2,
            "ingredients_text": 1.0,
            "categories_clean": 0.8,
            "categories": 0.5,
        }
    )

    completeness_weight: float = 0.15
