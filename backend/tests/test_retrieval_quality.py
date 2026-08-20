import socket

import pytest

from evaluation.evaluate import DuckDBSearchRepository
from query.dictionaries import load_dynamic_dictionaries
from repositories.opensearch_repository import OpenSearchSearchRepository
from retrieval.search_engine import SearchEngine

pytestmark = pytest.mark.evaluation


def _engine_available() -> bool:
    try:
        with socket.create_connection(("localhost", 9200), timeout=0.1):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


@pytest.fixture(scope="module")
def search_engine():
    # Fast check if OpenSearch port 9200 is open
    if _engine_available():
        try:
            repo = OpenSearchSearchRepository()
            return SearchEngine(repository=repo)
        except Exception:
            pass

    # Fallback to local DuckDB repository over the 114k Canadian OFF dataset
    repo = DuckDBSearchRepository()
    return SearchEngine(repository=repo)


def test_retrieval_numeric_constraint_protein(search_engine):
    load_dynamic_dictionaries()
    query = "products with at least 20g protein"
    res = search_engine.search(query, size=10)

    # Constraint queries MUST return results over the full 114k dataset.
    assert res.total >= 1, "Expected at least one hit for protein constraint query"
    for hit in res.hits:
        nut_dict = hit.product.attributes.get("nutrition", {})
        protein = nut_dict.get("proteins", {}).get("per_100g", 0)
        assert protein >= 20.0, "Product %s failed constraint" % hit.product.product_name


def test_retrieval_numeric_constraint_calories(search_engine):
    query = "snacks under 200 calories"
    res = search_engine.search(query, size=10)

    assert res.total >= 1, "Expected at least one hit for calorie constraint query"
    for hit in res.hits:
        nut_dict = hit.product.attributes.get("nutrition", {})
        cals = nut_dict.get("energy-kcal", {}).get("per_100g", 9999)
        assert cals <= 200.0, "Product %s failed constraint" % hit.product.product_name


def test_retrieval_boolean_negation_palm_oil(search_engine):
    query = "palm oil free peanut butter"
    res = search_engine.search(query, size=10)

    assert res.total >= 1, "Expected at least one hit for palm-oil-free query"
    for hit in res.hits:
        # Should not have palm oil
        flags = hit.product.attributes.get("flags", {})
        is_palm_oil_free = flags.get("is_palm_oil_free")
        assert is_palm_oil_free is True, "Product %s is not palm oil free" % (
            hit.product.product_name
        )
        ingredients = (hit.product.ingredients or "").lower()
        assert "palm oil" not in ingredients, (
            "Product %s contains palm oil in text" % hit.product.product_name
        )


def test_retrieval_exact_phrase_preservation(search_engine):
    # This ensures fuzziness fallback doesn't retrieve wild matches for exact phrases
    res = search_engine.search("peanut butter", size=5)
    assert res.total >= 1, "Expected hits for 'peanut butter'"
    for hit in res.hits:
        name = (hit.product.product_name or "").lower()
        search_text = (hit.product.search_text or "").lower()

        # Generic searches must surface products that actually contain both terms.
        in_name = name
        in_text = search_text
        assert "peanut" in in_name or "peanut" in in_text, (
            "Top result %r lacks 'peanut'" % hit.product.product_name
        )
        assert "butter" in in_name or "butter" in in_text, (
            "Top result %r lacks 'butter'" % hit.product.product_name
        )
