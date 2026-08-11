from unittest.mock import patch, MagicMock
import pandas as pd

from adapters.off_adapter import OFFAdapter
from models.raw_product import RawProduct
from models.search_document import SearchDocument
from pipeline.load import write_normalized_parquet_batch, read_normalized_parquet_with_nutriments
from pipeline.runner import run_pipeline


class TestOFFAdapterExtraction:
    @patch("duckdb.connect")
    @patch("pathlib.Path.exists", return_value=True)
    def test_adapter_yields_raw_products(self, mock_exists, mock_connect):
        mock_con = MagicMock()
        mock_connect.return_value = mock_con

        # Mock duckdb stream fetch chunk
        mock_con.execute.return_value.fetchmany.side_effect = [
            [
                (
                    "001",
                    "Test Product",
                    "Test Brand",
                    "Test Category",
                    "Test Ingredients",
                    "[{'name': 'energy', 'value': 200.0, '100g': 200.0, 'unit': 'kcal'}]",
                    "a",
                    1,
                    "b",
                    0.95,
                )
            ],
            [],  # Empty to terminate stream
        ]

        adapter = OFFAdapter("dummy.csv")
        results = list(adapter.extract_raw_products())

        assert len(results) == 1
        raw_prod = results[0]
        assert isinstance(raw_prod, RawProduct)
        assert raw_prod.code == "001"
        assert raw_prod.product_name == "Test Product"
        assert raw_prod.nutriments["energy"]["value"] == 200.0


class TestPipelineParquetLoad:
    def test_parquet_roundtrip_with_submodels(self, tmp_path):
        from config.settings import settings

        settings.processed_dir = tmp_path

        doc = SearchDocument(
            id="0008577002786",
            product_name="Organic Vermont Maple Syrup",
            brand="Butternut Mountain Farm",
            category="Sweeteners",
            ingredients="Pure organic maple syrup",
            attributes={
                "nutrition": {"energy": {"value": 1.0}},
                "flags": {"is_organic": True}
            },
            metadata={"completeness": 0.6625},
            search_text="text",
            semantic_document="sem",
        )

        output_path, writer = write_normalized_parquet_batch([doc])
        writer.close()
        assert output_path.exists()

        df = read_normalized_parquet_with_nutriments()
        assert len(df) == 1
        assert df.iloc[0]["id"] == "0008577002786"
        # Verify submodel values are restored
        assert df.iloc[0]["attributes"]["flags"]["is_organic"] is True
        assert df.iloc[0]["metadata"]["completeness"] == 0.6625
