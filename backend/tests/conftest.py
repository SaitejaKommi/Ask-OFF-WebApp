from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import get_search_engine
from models.search import SearchResponse, SearchHit
from models.search_document import SearchDocument


@pytest.fixture
def sample_raw_product_name() -> str:
    return (
        "[{'lang': 'main', 'text': 'Organic Vermont Maple Syrup'}\n"
        " {'lang': 'fr', 'text': \"Sirop d'erable bio du Vermont\"}\n"
        " {'lang': 'en', 'text': 'Organic Vermont Maple Syrup'}]"
    )


@pytest.fixture
def sample_raw_ingredients() -> str:
    return (
        "[{'lang': 'main', 'text': 'Pure organic maple syrup'}\n"
        " {'lang': 'en', 'text': 'Pure organic maple syrup'}]"
    )


@pytest.fixture
def sample_raw_nutriments() -> str:
    return (
        "[{'name': 'energy', 'value': 333.0, '100g': 1393.0, 'unit': 'kcal'}\n"
        " {'name': 'fat', 'value': 0.0, '100g': 0.0, 'unit': 'g'}]"
    )


@pytest.fixture
def sample_normalized_product() -> dict:
    return {
        "id": "0008577002786",
        "product_name": "Organic Vermont Maple Syrup",
        "brand": "Butternut Mountain Farm",
        "category": "Sweeteners,Syrups",
        "ingredients": "Pure organic maple syrup",
        "attributes": {
            "nutrition": {
                "energy": {"value": 333.0, "per_100g": 1393.0, "unit": "kcal"},
            },
            "flags": {"is_organic": True, "is_vegan": False, "is_vegetarian": False},
        },
        "metadata": {
            "nutriscore_grade": "e",
            "nova_group": 2,
            "ecoscore_grade": "b",
            "completeness": 0.6625,
        },
        "search_text": (
            "Organic Vermont Maple Syrup Butternut Mountain Farm "
            "Sweeteners,Syrups Pure organic maple syrup"
        ),
        "semantic_document": (
            "Product: Organic Vermont Maple Syrup\n\n"
            "Brand: Butternut Mountain Farm\n\n"
            "Category: Sweeteners,Syrups\n\n"
            "Ingredients:\nPure organic maple syrup"
        ),
    }


@pytest.fixture
def mock_search_engine() -> MagicMock:
    engine = MagicMock()
    product = SearchDocument(
        id="0008577002786",
        product_name="Organic Vermont Maple Syrup",
        brand="Butternut Mountain Farm",
        category="Sweeteners,Syrups",
        ingredients="Pure organic maple syrup",
        attributes={
            "nutrition": {
                "energy": {"value": 333.0, "per_100g": 1393.0, "unit": "kcal"}
            },
            "flags": {
                "is_organic": True,
                "is_vegan": False,
                "is_vegetarian": False
            }
        },
        metadata={
            "nutriscore_grade": "e",
            "nova_group": 2,
            "ecoscore_grade": "b",
            "completeness": 0.6625,
        },
        search_text=(
            "Organic Vermont Maple Syrup Butternut Mountain Farm "
            "Sweeteners,Syrups Pure organic maple syrup"
        ),
        semantic_document=(
            "Product: Organic Vermont Maple Syrup\n\n"
            "Brand: Butternut Mountain Farm\n\n"
            "Category: Sweeteners,Syrups\n\n"
            "Ingredients:\nPure organic maple syrup"
        ),
    )
    engine.search.return_value = SearchResponse(
        total=1,
        hits=[SearchHit(score=1.0, product=product)],
        query="maple syrup",
        took_ms=5,
    )
    engine.get_product.return_value = product
    engine.autocomplete.return_value = ["Organic Vermont Maple Syrup"]
    return engine


@pytest.fixture
def test_app(mock_search_engine: MagicMock):
    app = create_app()
    app.dependency_overrides[get_search_engine] = lambda: mock_search_engine
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(test_app):
    return TestClient(test_app)

