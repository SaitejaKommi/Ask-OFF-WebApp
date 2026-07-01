from models.product import NormalizedProduct
from pipeline.load import read_normalized_parquet
from .search_service import SearchService


class ProductService:
    def __init__(self) -> None:
        self.search_service = SearchService()

    def get_by_code(self, code: str) -> NormalizedProduct | None:
        response = self.search_service.get_product(code)
        if response is None:
            return None
        return NormalizedProduct(
            code=response.code,
            product_name=response.product_name,
            product_name_clean="",
            brands=response.brands,
            brands_clean="",
            categories=response.categories,
            categories_clean="",
            ingredients_text=response.ingredients_text,
            ingredients_clean="",
            nutriments=response.nutriments,
            nutriscore_grade=response.nutriscore_grade,
            nova_group=response.nova_group,
            ecoscore_grade=response.ecoscore_grade,
            completeness=response.completeness,
            search_text="",
            semantic_document="",
        )

    def get_analytics_dataframe(self):
        return read_normalized_parquet()
