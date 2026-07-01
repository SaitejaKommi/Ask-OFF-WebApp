import pandas as pd
from unittest.mock import patch, MagicMock

from pipeline.extract import extract_required_fields
from pipeline.load import write_normalized_parquet, read_normalized_parquet
from pipeline.normalizers import normalize_product_name
from models.product import NormalizedProduct


class TestExtract:
    @patch("duckdb.connect")
    @patch("pathlib.Path.exists", return_value=True)
    def test_extract_reads_required_columns(self, mock_exists, mock_connect):
        mock_con = MagicMock()
        mock_connect.return_value = mock_con

        mock_df = pd.DataFrame(
            {
                "code": ["001"],
                "product_name": ["test"],
                "brands": [""],
                "categories": [""],
                "ingredients_text": [""],
                "nutriments": [""],
                "nutriscore_grade": [None],
                "nova_group": [None],
                "ecoscore_grade": [None],
                "completeness": ["0.5"],
            }
        )
        mock_con.execute.return_value.fetchdf.return_value = mock_df

        result = extract_required_fields("dummy.csv")
        assert len(result) == 1
        assert result.iloc[0]["code"] == "001"

    def test_raises_on_missing_file(self):
        try:
            extract_required_fields("nonexistent.csv")
            assert False, "Should have raised"
        except FileNotFoundError:
            pass


class TestNormalizedProduct:
    def test_normalized_product_creation(self, sample_raw_product_name):
        original, cleaned = normalize_product_name(sample_raw_product_name)
        product = NormalizedProduct(
            code="0008577002786",
            product_name=original,
            product_name_clean=cleaned,
            brands="Butternut Mountain Farm",
            brands_clean="Butternut Mountain Farm",
            categories="Sweeteners",
            categories_clean="Sweeteners",
            ingredients_text="Pure organic maple syrup",
            ingredients_clean="Pure organic maple syrup",
            nutriments={"energy": {"value": 333.0}},
            nutriscore_grade="e",
            nova_group=2,
            ecoscore_grade="b",
            completeness=0.6625,
            search_text=(
                "Organic Vermont Maple Syrup Butternut Mountain Farm "
                "Sweeteners Pure organic maple syrup"
            ),
            semantic_document="Product: Organic Vermont Maple Syrup",
        )
        assert product.code == "0008577002786"
        assert product.product_name_clean == "Organic Vermont Maple Syrup"

    def test_normalized_product_defaults(self):
        product = NormalizedProduct(
            code="001",
            product_name="",
            product_name_clean="",
            brands="",
            brands_clean="",
            categories="",
            categories_clean="",
            ingredients_text="",
            ingredients_clean="",
            nutriments={},
            search_text="",
            semantic_document="",
        )
        assert product.completeness == 0.0
        assert product.nutriscore_grade is None
        assert product.nova_group is None


class TestLoad:
    def test_write_and_read_roundtrip(self, tmp_path, sample_normalized_product):
        from config.settings import settings

        settings.processed_dir = tmp_path

        products = [NormalizedProduct(**sample_normalized_product)]
        output_path = write_normalized_parquet(products)
        assert output_path.exists()

        df = read_normalized_parquet()
        assert len(df) == 1
        assert df.iloc[0]["code"] == "0008577002786"
