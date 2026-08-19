import socket
import pytest
from query.pipeline import SearchQueryPipeline
from retrieval.search_engine import SearchEngine
from repositories.opensearch_repository import OpenSearchSearchRepository
from evaluation.evaluate import DuckDBSearchRepository

@pytest.fixture(scope="module")
def search_engine():
    # Fast check if OpenSearch port 9200 is open
    opensearch_online = False
    try:
        with socket.create_connection(("localhost", 9200), timeout=0.1):
            opensearch_online = True
    except (socket.timeout, ConnectionRefusedError, OSError):
        opensearch_online = False

    if opensearch_online:
        try:
            repo = OpenSearchSearchRepository()
            return SearchEngine(repository=repo)
        except Exception:
            pass

    # Fallback to local DuckDB repository over the 114k Canadian OFF dataset
    repo = DuckDBSearchRepository()
    return SearchEngine(repository=repo)



def test_retrieval_numeric_constraint_protein(search_engine):
    query = "products with at least 20g protein"
    res = search_engine.search(query, size=10)
    
    # It's possible the small dataset has no results, but if it does, they MUST satisfy the constraint.
    for hit in res.hits:
        nut_dict = hit.product.attributes.get("nutrition", {})
        protein = nut_dict.get("proteins", {}).get("per_100g", 0)
        assert protein >= 20.0, f"Product {hit.product.product_name} failed constraint"

def test_retrieval_numeric_constraint_calories(search_engine):
    query = "snacks under 200 calories"
    res = search_engine.search(query, size=10)
    
    for hit in res.hits:
        nut_dict = hit.product.attributes.get("nutrition", {})
        cals = nut_dict.get("energy-kcal", {}).get("per_100g", 9999)
        assert cals <= 200.0, f"Product {hit.product.product_name} failed constraint"

def test_retrieval_boolean_negation_palm_oil(search_engine):
    query = "palm oil free peanut butter"
    res = search_engine.search(query, size=10)
    
    for hit in res.hits:
        # Should not have palm oil
        flags = hit.product.attributes.get("flags", {})
        is_palm_oil_free = flags.get("is_palm_oil_free")
        assert is_palm_oil_free is True, f"Product {hit.product.product_name} is not palm oil free"
        ingredients = (hit.product.ingredients or "").lower()
        assert "palm oil" not in ingredients, f"Product {hit.product.product_name} contains palm oil in text"

def test_retrieval_exact_phrase_preservation(search_engine):
    # This ensures fuzziness fallback doesn't retrieve wild matches for exact phrases
    res = search_engine.search("peanut butter", size=5)
    for hit in res.hits:
        name = (hit.product.product_name or "").lower()
        search_text = (hit.product.search_text or "").lower()
        
        # In a generic search, exact matches or strong AND matches should dominate.
        # It's hard to definitively assert recall without knowing the dataset, 
        # but if we get "Reese's", it should have "peanut butter" in search_text.
        # We can assert that the top result is highly relevant.
        if res.total > 0 and hit == res.hits[0]:
            assert "peanut" in search_text
            assert "butter" in search_text
