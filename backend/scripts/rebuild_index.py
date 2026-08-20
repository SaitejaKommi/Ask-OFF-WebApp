"""Rebuild the full "askoff_products" OpenSearch index from the canonical dataset.

Deletes the existing index, re-ingests all products from data/raw/normalized.parquet
through OFFAdapter -> SearchDocumentBuilder, and prints runtime metrics
(attempted vs indexed vs count, docs with nutrition, throughput, size, health).

Usage:
    python scripts/rebuild_index.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.off_adapter import OFFAdapter  # noqa: E402
from builders.search_document_builder import SearchDocumentBuilder  # noqa: E402
from config.settings import settings  # noqa: E402
from search import indexer  # noqa: E402
from search.client import get_client  # noqa: E402

settings.pipeline_batch_size = 5000

client = get_client()
index_name = settings.opensearch_index

t0 = time.time()
print(f"START: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t0))}")
if client.indices.exists(index=index_name):
    client.indices.delete(index=index_name)
    print("deleted old index")
indexer.ensure_index(client)

adapter = OFFAdapter()
builder = SearchDocumentBuilder()
total_ok = 0
total_docs = 0
batch = []
docs_with_nutrition = 0
for raw in adapter.extract_raw_products():
    doc = builder.build(raw)
    total_docs += 1
    if doc.attributes.get("nutrition"):
        docs_with_nutrition += 1
    batch.append(doc)
    if len(batch) >= settings.pipeline_batch_size:
        total_ok += indexer.index_products(batch)
        batch = []
if batch:
    total_ok += indexer.index_products(batch)

dt = time.time() - t0
print(f"END: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}")
client.indices.refresh(index=index_name)
cnt = client.count(index=index_name)["count"]
store = client.indices.stats(index=index_name)["indices"][index_name]["total"]["store"][
    "size_in_bytes"
]
health = client.cluster.health(index=index_name)["status"]
print(f"DOCUMENTS ATTEMPTED: {total_docs}")
print(f"DOCUMENTS INDEXED (bulk ok): {total_ok}")
print(f"INDEX COUNT: {cnt}")
print(f"DOCS WITH NUTRITION (pipeline): {docs_with_nutrition}/{total_docs}")
print(f"ELAPSED: {dt:.1f}s")
print(f"THROUGHPUT: {total_ok / dt:.0f} docs/s")
print(f"INDEX SIZE: {store / 1024 / 1024:.1f} MiB | HEALTH: {health}")

# sample nutrition from index
res = client.search(
    index=index_name,
    body={
        "size": 3,
        "query": {"match_all": {}},
        "_source": ["product_name", "attributes.nutrition"],
    },
)
for h in res["hits"]["hits"]:
    src = h["_source"]
    nut = src.get("attributes", {}).get("nutrition", {})
    print("idx doc:", src.get("product_name", "")[:50], "| nutrition keys:", list(nut.keys())[:6])
