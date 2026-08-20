"""
Integration test for NLP semantics against a real OpenSearch instance.
Creates a disposable index `askoff_test_semantics`, indexes 4 specific products,
runs semantic tests, and cleans up.
"""
import json
import sys

sys.path.insert(0, 'backend')

from models.search_document import SearchDocument
from repositories.opensearch_repository import OpenSearchSearchRepository
from retrieval.search_engine import SearchEngine
from search.mappings import PRODUCT_INDEX_MAPPING

INDEX_NAME = "askoff_test_semantics"

def setup_index(client):
    if client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)
    client.indices.create(index=INDEX_NAME, body=PRODUCT_INDEX_MAPPING)

def index_products(client):
    products = [
        SearchDocument(
            id="1",
            dataset_id="test",
            product_name="Product A - PB No Sugar",
            brand="Brand A",
            category="peanut butter",
            ingredients="peanuts, salt",
            attributes={"flags": {"is_low_sugar": True, "is_high_protein": False, "is_vegan": True}},
            metadata={"completeness": 1.0},
            search_text="peanut butter",
            semantic_document="peanut butter"
        ),
        SearchDocument(
            id="2",
            dataset_id="test",
            product_name="Product B - PB with Sugar",
            brand="Brand B",
            category="peanut butter",
            ingredients="peanuts, sugar, salt",
            attributes={"flags": {"is_low_sugar": False, "is_high_protein": True, "is_vegan": True}},
            metadata={"completeness": 1.0},
            search_text="peanut butter sugar",
            semantic_document="peanut butter sugar"
        ),
        SearchDocument(
            id="3",
            dataset_id="test",
            product_name="Product C - Chocolate",
            brand="Brand C",
            category="chocolate",
            ingredients="cocoa, sugar",
            attributes={"flags": {"is_low_sugar": False, "is_high_protein": False, "is_vegan": False}},
            metadata={"completeness": 1.0},
            search_text="chocolate cocoa sugar",
            semantic_document="chocolate cocoa sugar"
        ),
        SearchDocument(
            id="4",
            dataset_id="test",
            product_name="Product D - Vegan PB Low Sugar",
            brand="Brand D",
            category="peanut butter",
            ingredients="peanuts",
            attributes={"flags": {"is_low_sugar": True, "is_high_protein": False, "is_vegan": True}},
            metadata={"completeness": 1.0},
            search_text="vegan peanut butter",
            semantic_document="vegan peanut butter"
        )
    ]

    for p in products:
        client.index(index=INDEX_NAME, id=p.id, body=p.model_dump())

    client.indices.refresh(index=INDEX_NAME)

def run_tests():
    from search.client import get_client
    client = get_client()

    print("Setting up index...")
    setup_index(client)
    index_products(client)

    # We must patch the repository to use our test index
    repo = OpenSearchSearchRepository(client=client)
    repo.index = INDEX_NAME
    engine = SearchEngine(repository=repo)

    # Make sure dictionaries are loaded with our mock values so EntityExtractor works
    from query import dictionaries
    dictionaries.INGREDIENTS.update({"sugar", "peanut butter", "chocolate", "peanuts"})
    dictionaries.CATEGORIES.update({"peanut butter", "chocolate"})

    print("\n--- Running semantic tests ---")

    query = "low sugar peanut butter"
    print(f"\nQuery: {query}")
    res = engine.search(query, explain=True)

    print(f"Parsed query text term: {res.search_query.get('parsed_query')}")
    print(f"Extracted entities: {res.search_query.get('extracted_entities')}")
    print(f"Constraints applied: {res.search_query.get('constraints')}")

    print(f"\nResults: {res.total} found")
    for hit in res.hits:
        print(f"- {hit.product.product_name}")

    print("\nOpenSearch DSL MUST clauses:")
    musts = res.search_query.get("opensearch_query", {}).get("query", {}).get("function_score", {}).get("query", {}).get("bool", {}).get("must", [])
    for m in musts:
        print(f"  {json.dumps(m)}")

    # Validation
    returned_ids = {h.product.id for h in res.hits}
    if "1" in returned_ids and "4" in returned_ids and "3" not in returned_ids:
        print("\nSUCCESS: Returned only low sugar peanut butter products without forcing 'sugar' as ingredient.")
    else:
        print("\nFAILED: Incorrect products returned.")

    print("\nCleaning up...")
    client.indices.delete(index=INDEX_NAME)
    print("Done.")

if __name__ == "__main__":
    run_tests()
