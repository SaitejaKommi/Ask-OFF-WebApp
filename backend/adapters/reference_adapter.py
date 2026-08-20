from typing import Iterable

from adapters.base import BaseAdapter
from models.raw_product import RawProduct


class ReferenceAdapter(BaseAdapter):
    def extract_raw_products(self, limit: int | None = None) -> Iterable[RawProduct]:
        mock_products = [
            RawProduct(
                code="ref-10001",
                product_name="Reference Organic Honey",
                brands="Nature Honey",
                categories="Sweeteners, Honey",
                ingredients_text="Organic raw honey",
                nutriments={"energy": {"value": 304.0, "per_100g": 304.0, "unit": "kcal"}},
                nutriscore_grade="c",
                nova_group=1,
                ecoscore_grade="a",
                completeness=0.9
            ),
            RawProduct(
                code="ref-10002",
                product_name="Reference Almond Milk",
                brands="Silk Almond",
                categories="Beverages, Milk substitutes",
                ingredients_text="Almondmilk (filtered water, almonds), calcium carbonate, sea salt",
                nutriments={"energy": {"value": 30.0, "per_100g": 30.0, "unit": "kcal"}},
                nutriscore_grade="a",
                nova_group=3,
                ecoscore_grade="b",
                completeness=0.85
            )
        ]

        count = 0
        for p in mock_products:
            if limit is not None and count >= limit:
                break
            yield p
            count += 1
