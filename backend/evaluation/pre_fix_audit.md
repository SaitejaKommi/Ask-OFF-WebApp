# AskOFF P3 — PRE-FIX AUDIT

Snapshot taken BEFORE any implementation change. Baseline metrics from live OpenSearch:
**P@5 65.71% · P@10 64.00% · NDCG@10 85.72% · MRR 0.762 · Avg 78.11ms · P50 74.40ms · P95 155.26ms**
(35-query benchmark, 114,453-product Canadian OFF index.)

---

## 1. Current Architecture

Pure lexical, classical IR pipeline. No embeddings/vector/RAG/LLM.

```
backend/
  query/            NLP preconditioning (normalize -> constraints -> intent -> entities)
  retrieval/        SearchEngine (orchestrator) + ranking weights + filters + repository ABC
  repositories/     OpenSearchSearchRepository (builds DSL, executes, deserializes)
  search/           client + mappings + bulk indexer
  builders/         SearchDocumentBuilder (RawProduct -> SearchDocument + flags)
  adapters/         OFFAdapter / ReferenceAdapter / BaseAdapter
  pipeline/         extract/load/search_doc/runner
  evaluation/       evaluate.py (harness+labeler) + benchmark_queries.json
  api/              FastAPI routes + dependency singletons
  models/           RawProduct / SearchDocument / SearchHit / SearchResponse
```

Data flow: `OFFAdapter` reads `data/raw/normalized.parquet` (114,453 rows) → `SearchDocumentBuilder` →
bulk-indexed into `askoff_products` (OpenSearch 2.12.0, 1 shard / 1 replica, ~120 MiB). Index health yellow
(single-node replica unassigned — normal). All search goes through OpenSearch; DuckDB repo exists only for
offline benchmarking/tests.

## 2. Current Search Pipeline

`SearchEngine.search(query)`:
1. `SearchQueryPipeline.process(q)` — single static pipeline:
   - `QueryNormalizer.normalize`: lowercase, strip punctuation except `-`, collapse spaces.
   - `ConstraintExtractor.extract`: regex extraction of (a) modifiers [fresh, frozen, raw, pure, natural,
     wild, farmed, salted, unsalted], (b) numeric constraints (`under/less than/< 20g calories…` → gte/lte
     per_100g), (c) recipe quantities (ml/cup/tbsp/tsp/g/oz…), (d) dietary flags
     (organic/vegan/vegetarian/high_protein/low_sugar/…). Each removes its matched text from the query.
   - `IntentDetector.detect(cleaned)`: lexical patterns → `brand_search` / `category_browse` /
     `ingredient_search` / `generic_search`. Example: `by brand X` → brand_search; `under category Y` →
     category_browse; otherwise generic.
   - `EntityExtractor.extract(cleaned, intent)`: n-grams (up to 4) matched against static dictionaries
     (`backend/data/dictionaries.json`: 12,000 brands / 6,000 categories / 15,001 ingredients) plus small
     static sets for allergens/sustainability/nutrition/countries.
   - Produces `SearchQuery` (text_term, intent, entities, filters, numeric_filters, modifiers,
     recipe_quantities, pagination, metadata).
2. `SearchEngine` merges explicit API filters, then **conditionally** converts entities into retrieval
   filters:
   - brand entity → `filters["brand"]` ONLY if `intent == brand_search` or explicit API `brand` param.
   - category entity → `filters["category"]` ONLY if `intent == category_browse` or explicit API param.
   - ingredient entity → `filters["ingredients"]` ONLY if `intent == ingredient_search` or explicit API param.
   - **Otherwise (generic intent) entities are ignored for filtering** — the full text term goes to search.
   - constraints → flag term filters (`constraint_to_filter` map → `attributes.flags.is_*`), palm oil special-case.

## 3. Current OpenSearch DSL Construction

`OpenSearchSearchRepository.search` builds, under `function_score(query, functions=[completeness fvf +0.15], boost_mode=sum)`:

- `bool`
  - `must`: brand/category/ingredients `match(operator:and)` when filters present; flag `term`s; numeric
    `range` on `attributes.nutrition.{field}.per_100g`; `match_all` fallback.
  - `should` (minimum 1 if query text): layered bool of **three multi_match**:
    1. `type=phrase` boost 10.0 (full query as one phrase)
    2. `operator=and` boost 5.0 (all tokens)
    3. `type=best_fields`, `fuzziness=AUTO`, `operator=or` boost 0.5 (any single token — the OR clause)
    plus `match(product_name){modifier, boost 2.0}` per modifier.
  - `must_not`: palm-oil negation.
- `minimum_should_match=1` on the outer bool; **no minimum_should_match inside the OR clause** (any single token satisfies it).

## 4. Current Ranking Signals

`retrieval/ranking.py:RankingManager`:
- field boosts: `product_name^3.0`, `brand^2.0`, `category^1.5`, `ingredients^1.2`, `search_text^1.0`
- `phrase_boost 10.0`, `and_match_boost 5.0`, `fuzzy_boost 0.5`, `modifier_boost 2.0`
- `completeness_factor 0.15` (`field_value_factor`, `boost_mode=sum`)

Effective ordering: single-token OR-powered fuzzy/first-term matches can enter top-10 because outer
`minimum_should_match=1` and the OR clause requires only ONE of the query tokens.

## 5. Current NLP Behavior

- **Synonyms: none anywhere.** No synonym filter, no query-side canonicalization. `soya` vs `soy`,
  `yoghurt` vs `yogurt` are disjoint tokens.
- Modifier extraction works (frozen/fresh/… become +2.0 name match).
- Numeric + recipe-quantity regexes work (except quantities are extracted but **dropped**, unused as
  filters — no `quantity` column exists in data; acceptable).
- `%` product names preserved (`2% milk`, `7up` survived; `7up` handled via recipe-qty guard).
- Brand detection: dictionary-based; a false-positive exists (`chips` is present in the brands dict,
  benign today because generic intent applies no brand filter).
- Entity extraction is greedy longest-n-gram-first with span-overlap suppression.

## 6. Current Benchmark Relevance Logic

`evaluation/evaluate.py:evaluate_product(product, item)`:
- returns 0 if any `disallowed_keywords` substring in `name+search_text`
- returns 0 if any `required_flags` mismatched on `attributes.flags`
- returns 0 if `relevant_brand` present and not in brand or name
- else ranks by `relevant_keywords` ratio (matched substrings across name/search_text/brand):
  ratio==1.0 → 3 (if all in name) else 2; ratio>=0.5 → 1; else 0.

**Critical defects found in this audit:**

1. **Synonyms-as-conjunctions.** Keyword lists are synonym bags treated as mandatory conjunctions
   (`coffee:[coffee,roast,espresso]`, `frozen vegetables:[frozen,vegetable,peas,corn,broccoli,blend]`,
   `tomato sauce:[tomato,sauce,pasta]`, `breakfast cereal:[cereal,granola,flakes,oats]`,
   `chocolate cookies:[chocolate,cookie,biscuit]`, `almond milk:[almond,milk,beverage]`,
   `low sugar cereal:[cereal,granola,oats]`, `high protein snacks:[snack,bar,nuts,protein]`).
2. **`nutrition_constraint` is never evaluated by the labeler.** `evaluate_product` ignores it;
   numeric-type queries with `relevant_keywords:[]` return 3 unconditionally (vacuous passes).
3. **EVOO disallowed collision.** `disallowed "vegetable oil"` substring-zeroes every EVOO whose OFF
   category path contains the token `Vegetable oils`.
4. `relevant_brand`/keywords checked against concatenated `search_text` (name+brand+category+ingredients)
   → a keyword present in the category chain inflates relevance.

## 7. Current Known Defects (reproduced live, see root-cause report)

| # | Defect | Evidence | Root files |
|---|--------|---------|-----------|
| D1 | `soya`/`soy` disjoint → true `Soya sauce`/Compliments outside top-50 of `compliments soy sauce` | live ranks | `search/mappings.py` (no synonyms), DSL phrase clause |
| D2 | Brand entity ignored under generic intent → no brand filter; `Soy Burgers` (brand-only+ingredient match) > real soy sauces | live top-10 | `retrieval/search_engine.py:74-84` |
| D3 | OR-clause single-token pollution (`minimum_should_match` unset) → brand-label docs, vegan-non-cookie docs fill slots | `Compliments strawberry…` ranks 3–7; `vegan cookies` ranks 3–5 | `repositories/opensearch_repository.py:73-84` |
| D4 | Benchmark labeler: synonym conjunctions → 10/15 analyzed queries mislabeled | label matrix | `evaluation/evaluate.py:299-344` + `benchmark_queries.json` |
| D5 | Benchmark ignores `nutrition_constraint` (vacuous numeric passes) | labeler code | `evaluation/evaluate.py:299-344` |
| D6 | EVOO disallowed `vegetable oil` taxonomy collision | top-1 Gallo EVOO rel0 | `evaluation/evaluate.py` + benchmark item |

## 8. Current Baseline Metrics (preserved)

```
ORIGINAL BASELINE (35 queries, live OpenSearch, 114,453 docs)
P@5      65.71%
P@10     64.00%
NDCG@10  85.72%
MRR      0.762
Avg      78.11 ms   P50 74.40 ms   P95 155.26 ms
```

## 9. Exact Files/Functions Responsible

- Synonym gap: `backend/search/mappings.py` analyzers (no synonyms); query has no synonym step.
- Brand handoff: `backend/retrieval/search_engine.py` `search()` entity→filter gating (lines ~74–84).
- OR pollution: `backend/repositories/opensearch_repository.py` `search()` should-clause OR multi_match
  (no `minimum_should_match`), outer `minimum_should_match=1`.
- Benchmark labeler: `backend/evaluation/evaluate.py` `evaluate_product()` +
  `backend/evaluation/benchmark_queries.json` (keyword semantics, EVOO disallowed).
- Nutrition flags/thresholds: `backend/builders/search_document_builder.py` (is_low_sugar ≤5g, is_high_protein ≥10g — project-defined; to be preserved as semantics).
- Modifier/numeric/recipe extraction: `backend/query/constraint_extractor.py`.
- Entity extraction: `backend/query/entity_extractor.py` + `backend/data/dictionaries.json`.
- Pipeline: `backend/query/pipeline.py`; DSL: `backend/repositories/opensearch_repository.py`;
  ranking weights: `backend/retrieval/ranking.py`.