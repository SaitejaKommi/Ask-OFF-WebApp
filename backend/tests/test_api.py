from fastapi import status


class TestSearchEndpoint:
    def test_search_returns_200(self, test_client):
        response = test_client.get("/search", params={"q": "maple syrup"})
        assert response.status_code == status.HTTP_200_OK

    def test_search_returns_search_response_schema(self, test_client):
        response = test_client.get("/search", params={"q": "maple syrup"})
        data = response.json()
        assert "total" in data
        assert "hits" in data
        assert "query" in data
        assert "took_ms" in data

    def test_search_requires_q_param(self, test_client):
        response = test_client.get("/search")
        assert response.status_code == 422

    def test_search_respects_size_param(self, test_client):
        response = test_client.get("/search", params={"q": "test", "size": 50})
        assert response.status_code == status.HTTP_200_OK

    def test_search_rejects_invalid_size(self, test_client):
        response = test_client.get("/search", params={"q": "test", "size": 200})
        assert response.status_code == 422


class TestProductEndpoint:
    def test_get_product_returns_200(self, test_client):
        response = test_client.get("/products/0008577002786")
        assert response.status_code == status.HTTP_200_OK

    def test_get_product_returns_product_schema(self, test_client):
        response = test_client.get("/products/0008577002786")
        data = response.json()
        assert "code" in data
        assert "product_name" in data
        assert "brands" in data
        assert "categories" in data
        assert "completeness" in data

    def test_get_product_returns_404_for_missing(
        self, test_client, mock_search_service
    ):
        mock_search_service.get_product.return_value = None
        response = test_client.get("/products/nonexistent")
        assert response.status_code == 404


class TestBrandEndpoint:
    def test_search_brand_returns_200(self, test_client):
        response = test_client.get("/brands/Butternut")
        assert response.status_code == status.HTTP_200_OK

    def test_search_brand_returns_search_response(self, test_client):
        response = test_client.get("/brands/Butternut")
        data = response.json()
        assert "hits" in data
        assert "total" in data


class TestCategoryEndpoint:
    def test_search_category_returns_200(self, test_client):
        response = test_client.get("/categories/Sweeteners")
        assert response.status_code == status.HTTP_200_OK

    def test_search_category_returns_search_response(self, test_client):
        response = test_client.get("/categories/Sweeteners")
        data = response.json()
        assert "hits" in data
        assert "total" in data


class TestOpenSearchUnavailable:
    def test_search_returns_503_when_opensearch_down(
        self, test_app, mock_search_service
    ):
        from opensearchpy.exceptions import ConnectionError

        mock_search_service.search.side_effect = ConnectionError(
            "Connection refused", "", None
        )
        from fastapi.testclient import TestClient

        client = TestClient(test_app)
        response = client.get("/search", params={"q": "test"})
        assert response.status_code == 503
        data = response.json()
        assert "search_engine_unavailable" in data.get("error", "")
