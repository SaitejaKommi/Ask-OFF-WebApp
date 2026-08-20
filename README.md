# AskOFF — Open Food Facts Canada Search Backend

Search & Retrieval backend for Canadian Open Food Facts products (114,453 normalized
products). Lexical, explainable, offline-first — no external model or cloud services
required for search.

## Quick start (reproducible local setup)

Requirements: Docker (for OpenSearch), Python 3.11+ venv, ~120 MB disk for the dataset.

```
# 1. Start OpenSearch 2.x (single node)
docker compose up -d opensearch

# 2. Create venv and install
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt

# 3. Prepare the dataset (required only once)
#    Place the normalized Canada OFF parquet at data/raw/normalized.parquet
#    (see "Dataset" below) and then:
python backend/scripts/build_dictionaries.py            # static NLP dictionaries
python backend/scripts/rebuild_index.py                 # full 114k index + metrics

# 4. Run tests
cd backend && .venv\Scripts\python -m pytest -q

# 5. Benchmark (defaults to local DuckDB; use --repo opensearch for live cluster)
.venv\Scripts\python backend/evaluation/evaluate.py --repo opensearch

# 6. Start the API
.venv\Scripts\python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Architecture

```
data/raw/normalized.parquet  → OFFAdapter → SearchDocumentBuilder → OpenSearch "askoff_products"
                                                                        ↑
query text → NLP pipeline (normalize → tokenize → intent → entities → constraints
            → numeric filters → modifiers → recipe quantities) → SearchEngine
            → OpenSearch (tiered multi_match + filter_bool + function_score)

Layers: data/ -> config/ -> search/ -> repositories/ -> retrieval/ -> query/ -> api/
```

Key modules:

| File | Responsibility |
|---|---|
| `data/adapters/off_adapter.py` | Dataset ingestion (CSV or Parquet auto-detect) |
| `data/pipeline/runner.py` | Indexing pipeline orchestration |
| `builders/search_document_builder.py` | Product → index document + nutrition/flags |
| `utils/off_parser.py` | `parse_nutriments` (JSON-style, list-style, malformed-safe) |
| `query/pipeline.py` | NLP query → structured `SearchQuery` |
| `query/dictionaries.py` | Entity dictionaries (static JSON first, OpenSearch fallback) |
| `retrieval/search_engine.py` | Orchestrates filters + text retrieval |
| `repositories/opensearch_repository.py` | Live OpenSearch DSL (single implementation used in prod) |
| `evaluation/` | 35-query benchmark harness + `benchmark_queries.json` |
| `api/` | FastAPI app (`/search`, `/product/{id}`, `/brand`, `/category`, `/ingredient`, ...) |

## API

```
GET /search?q=<query>&size=20&explain=true     # explain=true returns the parsed query,
                                               # constraints, numeric filters, and the
                                               # exact OpenSearch DSL sent to the cluster
GET /product/{barcode}
GET /brand/{brand} | /category/{category} | /ingredient/{ingredient}
GET /autocomplete?q=... | /suggestions?q=...
GET /compare?ids=<barcode>&ids=<barcode>
GET /health (or root "/" → status + document_count)
```

Example:

```
GET /search?q=frozen+blueberries&explain=true
  → hits[0] = Frozen Blueberries (P@5 = 1.0 for the recipe-quantity query
    "500 mL (2 cups) frozen blueberries")
```

## Evaluation

`evaluation/evaluate.py` runs the 35-query benchmark and reports P@5, P@10, NDCG@10,
MRR and latency, broken down by query category (product, recipe_ingredient, dietary,
nutrition_numeric, brand_product, ...). Two backends are supported; the same tiered
multi-match scoring rules are implemented in both:

```
python backend/evaluation/evaluate.py                # DuckDB over 114k parquet (offline)
python backend/evaluation/evaluate.py --repo opensearch   # live full index
```

Reference (live OpenSearch, full 114,453-doc index, P3 hardening build):

| Metric | Value |
|---|---|
| Precision@5 | ~66% |
| Precision@10 | ~64% |
| NDCG@10 | ~86% |
| MRR | ~0.76 |
| Latency p50 / p95 | ~77 ms / ~240 ms |
| Index size | ~110 MiB (yellow health, 1 replica unassigned — expected single node) |

The `nutrition` and `nutrition_numeric` query classes validate the dietary-flag and
numeric-constraint paths. Runtime verification gates every claim: rebuild script
prints attempted vs indexed vs `count`, and the retrieval-quality tests assert every
returned hit satisfies its constraint.

## Testing

```
cd backend
.venv\Scripts\python -m pytest -q            # 76 tests (unit + integration + evaluation)
.venv\Scripts\python -m pytest -m unit -q    # fast offline-only subset
.venv\Scripts\python -m pytest -m evaluation -q
```

Markers: `unit`, `integration`, `evaluation` (see `pyproject.toml`).

Lint: `.venv\Scripts\python -m ruff check backend` (E, F, I, N, W rules).
Format: `.venv\Scripts\python -m black backend`.

## Commands

| Task | Command |
|---|---|
| Rebuild full index (delete + reindex 114k, prints metrics) | `python backend/scripts/rebuild_index.py` |
| Rebuild NLP dictionaries | `python backend/scripts/build_dictionaries.py` |
| Benchmark | `python backend/evaluation/evaluate.py [--repo opensearch]` |
| Tests | `cd backend && python -m pytest -q` |

## Dataset

- Source: Open Food Facts Canada export (normalized `normalized.parquet`).
- The canonical local copy is `data/raw/normalized.parquet` (~47 MB, 114,453 rows, gitignored).
- `backend/data/processed/normalized.parquet` is an equivalent copy used as a fallback.
- The root-level `data/raw/*.csv` and `data/processed/*.parquet` are 29-row dev samples;
  the adapter resolves the canonical path first, so the 114k dataset wins when present.
- Nutrient values are stored per-100g; numeric constraints (`at least 20g protein`,
  `under 200 calories`, ...) are enforced as OpenSearch range filters on
  `attributes.nutrition.<nutrient>.per_100g`.

## Known limitations (honest, documented in the P3 audit)

1. `core_product_id` / `variant_id` — NOT YET AVAILABLE from the current data source
   (fields absent in the export; `barcode` is the identity today).
2. `high_protein` / `low_sugar` / `low_sodium` flags are derived via threshold rules
   on per-100g values plus category hints (e.g. "no sugar added"); they are NOT
   OFF-approved labels.
3. Nutrition records exist for 104,273 / 114,453 products (~91%). Products without a
   nutriments column entry are indexed but excluded from nutrient-constraint queries.
4. No semantic/vector/hybrid ranking — pure lexical tiered BM25, by design for P3
   (see "Roadmap").
5. `intent=brand_search` / `category_browse` / `ingredient_search` only fire on
   explicit patterns (`kroger`, `brand X`, `category Y`); passive brand mentions
   inside generic queries rank by relevance rather than filtering.
6. Duplicate SKUs (`2% milk`, `coffee`) exist in the dataset; dedup of equivalent
   products is part of the semantic roadmap.

## Roadmap (explicitly out of scope for P3)

- Semantic / hybrid retrieval (embeddings), product dedup, identifier resolution.
- Pre-computed dictionaries refresh automation (currently a build script; entity
  dictionaries are committed as `backend/data/dictionaries.json`).