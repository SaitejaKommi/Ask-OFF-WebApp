# P3 SEARCH QUALITY — ROOT CAUSE ANALYSIS

Scope: 13 weak benchmark queries run against **LIVE OpenSearch** (114,453-product index, `askoff_products`, 2.12.0).
Baseline from `python evaluation/evaluate.py --repo opensearch`: **P@5 65.71% · P@10 64.00% · NDCG@10 85.72% · MRR 0.762 · 78.11ms avg / 155ms p95**.

This is analysis only. No code was modified. Evidence snapshot: `audit_evidence/root_cause_raw.json`
(per-query normalized query, entities, constraints, numeric filters, modifiers, full OpenSearch DSL, top-10 hits with per-hit keyword-match matrix, flag checks, benchmark `rel` scores).

**Relevance labeler (from `evaluate.py:evaluate_product`)** — the single most important fact in this report:
a product is `rel≥2` only if **ALL** `relevant_keywords` are substring-present somewhere in
`name + search_text + brand`. Many keyword sets are **synonym lists treated as conjunctions** (e.g.
`["soya","soy","sauce"]`, `["coffee","roast","espresso"]`, `["frozen","vegetable","peas","corn","broccoli","blend"]`).
A product that matches only 1–2 of 3–6 keywords is scored `rel=0` when ratio < 0.5, `rel=1` when ≥ 0.5 but < 1.0.
This one mechanism explains the majority of "failures" below.

---

## EXECUTIVE SUMMARY

- **10 of 15 analyzed queries fail because of the benchmark labeler, not the engine.** The top-10 results are, by inspection, correct products; the labeler scores them `rel=0` because synonyms/example-terms are treated as mandatory conjunctions.
- **2 queries fail due to dataset coverage.** `Compliments strawberry cereal bars` (exactly **1** Compliments product exists) and `vegan cookies` (only **2** cookies carry the `is_vegan` flag in the whole index).
- **1 query fails due to a real retrieval defect: `Compliments soy sauce`.** The true product (`Soya sauce` / Compliments) ranks outside the top-50 because (a) `soya` does not tokenize to `soy`, and (b) soy sauce–containing patties outrank it via the Boolean-AND clause + brand match. A secondary query-construction gap (a recognized brand entity is never promoted to a brand filter) enables the pollution.
- **Nutrition constraints are real, verified, and correctly applied.** Both `low sugar` and `high protein` are converted to **term filters on `attributes.flags.Is_low_sugar / is_high_protein`** (binary thresholds: sugars ≤ 5 g/100 g; proteins ≥ 10 g/100 g). The numeric queries use **range filters** (`proteins.per_100g ≥ 20`, `energy-kcal.per_100g ≤ 200`). The success/failure split between these four queries is caused by **labeler keyword count**, not constraint handling.
- **Real engineering defects found: 3** (1 tokenization/retrieval, 1 query-construction OR pollution, 1 brand-intent promotion gap). Fixes are small and contained.

---

## QUERY-BY-QUERY ANALYSIS

Legend: score | product | brand → `rel` under the benchmark labeler. `rel`: 3/2 = relevant (P counts rel≥2), 1 marginal, 0 irrelevant.

### 1. `Compliments strawberry cereal bars` — P@5 0.20 / P@10 0.10 / MRR 1.00

**NLP:** normalized `compliments strawberry cereal bars` · intent `generic_search` · entities: brand=`compliments`, category=`strawberry cereal bars` · cleaned term unchanged · constraints {} · DSL: single OR bool of 3 multi_match clauses (phrase/and/fuzzy) over `name^3.0, brand^2.0, category^1.5, ingredients^1.2, search_text^1.0`; `minimum_should_match=1`; completeness `+0.15×`sum.

| # | score | product | brand | rel |
|---|-------|---------|-------|-----|
| 1 | 88.07 | Strawberry Cereal Bars | Compliments | **3** |
| 2 | 20.90 | Strawberry Cereal Bars | (none) | 0 |
| 3–7 | 15.2 | "compliments" (brand-label product, no name/cat) | Compliments | 0 |
| 8–10 | 14.6 | Strawberry Fruit Bars | Whole Fruit / none | 0 |

**Expected:** the Compliments strawberry cereal bar ranks #1 (it does). Realistically few other Compliments product exists.
**Error class:** DATA COVERAGE (primary) + ranking pollution secondary.
**Root cause:** Dataset contains **1** product `Strawberry Cereal Bars` by Compliments (verified in parquet). The benchmark tasks the engine with filling 10 slots from a 1-member target set. Ranks 3–7 are docs whose **only** match is the brand token (fuzzy OR clause, `minimum_should_match=1`).
**Signal responsible:** fuzzy match · data absence.
**Engine defect:** No (the #1 result is correct). Recommend (implementation phase) reading `minimum_should_match` upward for 4-token queries to drop single-token brand-label docs.
**Fix:** not required for correctness of #1; candidate for OR-pollution fix (see #2).

### 2. `Compliments soy sauce` — P@5 0.20 / P@10 0.10 / MRR 1.00  ⚠ REAL DEFECT

**NLP:** entities brand=`compliments`, ingredient=`soy sauce` · intent `generic_search` → **no brand filter is applied** (brand filters only activate for `intent=="brand_search"`, and IntentDetector returns `generic_search` for every brand+product query).

| # | score | product | brand | rel |
|---|-------|---------|-------|-----|
| 1 | **40.02** | **Soy Burgers** | Compliments | 2 |
| 2 | 21.91 | soy sauce soya | no name | 0 |
| 3 | 21.88 | Soy sauce Soya | (none) | 0 |
| 4–5 | 19.8/18.9 | Pepperoni / 3-Cheese Mini Pizzas | Compliments | 1 |
| 6 | 18.42 | Our Compliments Soy Burger | Our Compliments | 0 |
| 7–10 | 17.82 | Soy Sauce × 3 brands (Irresistible / Kikkoman / Marca Pina) | other | 0 |
| … | — | **Soya sauce** | **Compliments** | (outside top-50, score 16.5) |

**Expected:** `Soya sauce` / Compliments (verified present: `brand="compliments"`, name `"Soya sauce"`, score 16.47 under a controlled brand-filtered phrase query) should be #1. It is **out of the top 50** for the open query.
**Error class:** RETRIEVAL BUG (tokenization) + NLP/query-construction gap.
**Root cause, precisely:**
1. **`soya` ≠ `soy`.** The query's phrase clause (`multi_match type=phrase`) searches the literal phrase `"soy sauce"`. The true product is named **"Soya sauce"** (Canadian OFF spelling). It never matches the phrase clause, nor the AND clause (token `soy` missing). Only the fuzzy OR clause catches it (`best_fields`, boost 0.5) → ~16.5, below 10 other candidates.
2. **`Soy Burgers` wins via cross-field AND boost.** Its ingredients literally contain a `soy sauce` substring; query tokens `soy` (ingredients) + `sauce` (ingredients) + `compliments` (brand) all match across fields → the **AND-multi-match clause (boost 5.0)** fully scores → 40.02 ≈ 2.3× a pure phrase/no-brand match.
3. **Enabled by**: the extracted brand entity `compliments` is never compiled into a must-filter (intent stays `generic_search`), so "brand match only" is not separated from "brand match + product match". Kikkoman's `Soy Sauce` (17.82) is genuinely more on-product than a Compliments party, yet a Compliments soy-sauce burger beats every real soy sauce.
**Signal responsible:** fuzzy match / phrase mismatch (soya), AND boost (cross-field), missing brand filter (query construction).
**Engine defect:** Yes. Recommend in implementation phase:
- add `soya→soy` (and common OFF-CA/FR synonyms) at tokenization or query-rebuild stage for ingredient/product terms;
- when a brand entity AND a product/ingredient entity are both extracted, add the brand as a *must/match-all* (soft) filter;
- raise `minimum_should_match` for the OR clause on 3+ token queries to ≥2.

### 3. `chips` — P@5 0.40 / P@10 0.50 / NDCG 0.83 / MRR 1.00

**NLP:** normalized `chips` · entity: **`chips` matched the BRANDS dictionary** (data-side dictionary noise; harmless today, no filter applied for generic intent) · cleaned term `chips`.

| # | score | product | brand | rel |
|---|-------|---------|-------|-----|
| 1–10 | 281.4–281.37 | "Chips" (Ruffles, Lay's, President's Choice, No Name, Siete…) | various | 1–2 |

Top-10 are all genuine potato/tortilla chips. `rel=2` only where the product's category (in `search_text`) also contains "Crisps"; `rel=1` otherwise.
**Error class:** BENCHMARK LABEL PROBLEM.
**Root cause:** `relevant_keywords=["chip","crisp"]` — synonyms modeled as a conjunction; product must hit **both**. `rel≥2` requires ratio 1.0; `rel=1` requires ratio ≥ 0.5 → a doc with only "chip" is `rel=1` (not counted in P).
**Signal responsible:** incorrect relevance label.
**Fix:** none (engine). Labeler should treat keywords as OR-groups/synonym sets.

### 4. `coffee` — P@5 0.00 / P@10 0.00 / MRR 0.00

**NLP:** category entity `coffee` · no constraints · DSL is the standard 3-clause bool.

| # | score | product | brand | rel |
|---|-------|---------|-------|-----|
| 1 | 381.8 | Coffee Coffee Coffee | Righteous | 0 |
| 2–10 | ~333.7 | "Coffee" | Tim Hortons, PC, Kicking Horse, Tims, McDonald's… | 0 |

Every top-10 hit is literally "Coffee" — **perfect retrieval**. All scored 0 because keywords `["coffee","roast","espresso"]` require all three; plain "Coffee" matches 1/3.
**Error class:** BENCHMARK LABEL PROBLEM.
**Root cause:** 3-keyword conjunction where products named exactly "Coffee" (the ideal, high-quality results) match only one keyword. The labeler punishes the best results.
**Signal responsible:** incorrect relevance label.

### 5. `chocolate cookies` — P@5 0.20 / P@10 0.10 / NDCG 0.50

**NLP:** category entities `chocolate` + `cookies` · no filters.

| # | score | product | brand | rel |
|---|-------|---------|-------|-----|
| 1 | 442.5 | Chocolate Cookies | Meiji | 1 |
| 2–3 | 383.8 | Double Chocolate Cookies | Made Good | 1 / **2** |
| 4–10 | 383.7 | Triple/Double/Milk/Salted Chocolate Cookies | Zehrs, Seedwise,… | 1 |

All top-10 are chocolate cookies. `rel=2` appears only where category text contains "Biscuits" (all three keywords hit).
**Error class:** BENCHMARK LABEL PROBLEM.
**Root cause:** `["chocolate","cookie","biscuit"]` — `biscuit` is an English/French synonym forced as a third conjunction. Most chocolate-cookie names lack "biscuit".
**Signal responsible:** incorrect relevance label.

### 6. `vegan cookies` — P@5 0.40 / P@10 0.20 / MRR 1.00

**NLP:** constraint `vegan: true` (extracted), cleaned term `cookies` · DSL: `must: [term(attributes.flags.is_vegan=True)]` — **the constraint is a real filter**.

| # | score | product | rel |
|---|-------|---------|-----|
| 1–2 | 207 / 186 | Goji Berries & Chocolate Cookies / Heavenly Hunks | **2** | 
| 3–5 | 8.5 / 8.3 / 7.1 | Fusilli au poulet crémeux / MealBetix / Amy's Pizza (vegan, non-cookie) | 0 |

**Error class:** DATA COVERAGE (primary) + ranking noise (secondary).
**Root cause:** `is_vegan` flag exists on only **140 of 114,453 docs** (verified by index count) because OFF-CA rarely carries a "vegan" category/ingredient tag; of those, only **2 are cookies**. The filter correctly restricts to vegan products; the two true targets rank 1–2. Ranks 3–5 are vegan but non-cookie products admitted by the fuzzy OR clause (single-token match).
**Signal responsible:** data absence · fuzzy match (secondary).
**Engine defect:** no for the #1–2 placement.

### 7. `low sugar cereal` — P@5 0.00 / P@10 0.00  ⚠ CONSTRAINT CONFIRMED REAL

**NLP:** constraint `low_sugar: true` · cleaned term `cereal` · DSL: `must: [term(attributes.flags.is_low_sugar=True)]` + text `cereal`. Total 1,734.

| # | score | product | sugars(g/100g) | rel |
|---|-------|---------|----------------|-----|
| 1 | 330.7 | Cocca Cereal | **0.0** | 0 |
| 2 | 330.7 | Cereal Crackers | **5.0** | 0 |
| 5 | 287.0 | Protein Cereal Cocoa (Magic Spoon) | **0.0** | 0 |
| 6–10 | 286.9 | Cinnamon Toast Cereal, grain free cereal, 8 grain cereal… | ≤5 (flagged) | 0 |

**Error class:** BENCHMARK LABEL PROBLEM. Constraint handling is correct and **verified** (sample nutriments re-read from the index: Cocca Cereal sugars 0.0 g, Magic Spoon cocoa 0.0 g, Cereal Crackers 5.0 g — all satisfy ≤ 5 g).
**Root cause:** `relevant_keywords=["cereal","granola","oats"]` require all three. Real low-sugar cereals are named for their product, not for "granola/oats". 1/3 keywords → `rel=0`.
**Signal responsible:** incorrect relevance label. (`is_low_sugar` flag derived as `0 ≤ sugars ≤ 5` OR category phrase — index-side correct.)

### 8. `high protein snacks` — P@5 0.00 / P@10 0.00  ⚠ CONSTRAINT CONFIRMED REAL

**NLP:** constraint `high_protein: true` · cleaned term `snacks` · DSL: `must: [term(attributes.flags.is_high_protein=True)]` + text `snacks`. Total 1,082.

| # | score | product | protein(g/100g) | rel |
|---|-------|---------|----------------|-----|
| 1 | 358.9 | Chicken Snacks (Clover Leaf) | **10.1** | 0 |
| 2 | 358.9 | Kippered snacks | **21.0** | 0 |
| 3–9 | 358.9/358.8 | Seafood / Cashew / Fibre / Scallop / Fit snacks | ≥10 (flagged) | 0 |
| 10 | 311.5 | Pepperoni Pizza Snacks | ≥10 | 0 |

**Error class:** BENCHMARK LABEL PROBLEM. Constraint real and verified.
**Root cause:** `relevant_keywords=["snack","bar","nuts","protein"]` — **four** keywords, all required. The correct product (Chicken Snacks, 10.1 g protein) matches only `snack` (and protein is a flag, not a name token) → 1/4 → `rel=0`.
**Signal responsible:** incorrect relevance label + keyword list mixing the category ("snack") with ingredient examples ("bar/nuts") and the trait itself ("protein").

### 9. `products with at least 20g protein` — P@10 1.00 (succeeds — control)

**NLP:** numeric `protein ≥ 20 g/100g` · cleaned term `products with` · DSL: `must: [range(attributes.nutrition.proteins.per_100g {gte: 20.0})]`. Total 1,205. All top-10 (Corned Beef, Brie Double Crème, Oven Roasted Chicken…, verified ≥ 20 g or flagged high-protein) → `rel=3` because **keyword list is empty**.
**Why it succeeds:** numeric range filter (real) + no keyword conjunction in the labeler.

### 10. `snacks under 200 calories` — P@10 1.00 (succeeds — control)

**NLP:** numeric `energy ≤ 200 kcal/100g` + text `snacks` · DSL: `must: [range(attributes.nutrition.energy-kcal.per_100g {lte: 200.0})]`. Total 358. All top-10 → `rel=3` (single keyword `snack`, trivially satisfied).
**Why it succeeds:** identical to #8 except the labeler demands 1 keyword (`snack`) instead of 4.

### 11. `frozen vegetables` — P@5 0.00 / P@10 0.00

**NLP:** category entity `frozen vegetables`, modifier `frozen` (added as +2.0 name boost clause) · no category filter.

| # | score | product | rel |
|---|-------|---------|-----|
| 1 | 691.4 | Frozen vegetables (Bonduelle) | 0 |
| 2–4 | 599–529 | Ferma / California Style / Thai Mix Frozen Vegetables | 0 |
| 5–6 | 474 | California / Asian Style **Blend** Frozen Vegetables | 1 |
| 7–10 | 268–237 | Mixed Vegetables, Frozen / Pepper&Onion Blend / Brussels Sprouts | 0 |

**Error class:** BENCHMARK LABEL PROBLEM.
**Root cause:** `relevant_keywords=["frozen","vegetable","peas","corn","broccoli","blend"]`. The engine returns excellent frozen-vegetable products; the labeler requires **all six** tokens. "Frozen vegetables" (Bonduelle) hits 2/6 → `rel=0`. Only blends mentioning broccoli+blend hit 4/6 → `rel=1`. Worse: the single best product is scored lower than generic blends.
**Signal responsible:** incorrect relevance label (six-keyword conjunction).

### 12. `breakfast cereal` — P@5 0.00 / P@10 0.00

**NLP:** no category entity match (the CATEGORIES dictionary does not contain `breakfast cereal` as a phrase — `cereal` unigrams appear but the phrase was not boosted by a category clause). Text term `breakfast cereal` unchanged.

| # | score | product | category | rel |
|---|-------|---------|----------|-----|
| 1 | 455.5 | Original Breakfast Cereal Dragon's Blend | (none) | 0 |
| 2 | 299.7 | Cinnamon And Vanilla Shreddies | Breakfast Cereal | 0 |
| 3–10 | 83–56 | Harvest Crunch, Morning Crisp, LARGE FLAKE OATS, Granola… | cereal paths | 1 |

**Error class:** BENCHMARK LABEL PROBLEM.
**Root cause:** `relevant_keywords=["cereal","granola","flakes","oats"]` — all four required. The two most relevant results (name/category literally "Breakfast Cereal") match only `cereal` (1/4 → `rel=0`); granola/flakes/oats items get `rel=1`. **The labeler zeroes the exact matches.**
**Signal responsible:** incorrect relevance label.

### 13. `tomato sauce` — P@5 0.00 / P@10 0.00

**NLP:** ingredient entity `tomato sauce` · no filter · DSL: standard bool on full term. Total 7,535.

| # | score | product | rel |
|---|-------|---------|-----|
| 1–10 | 495.4–495.3 | "Tomato Sauce" (No Name, Founders&Farmers, La San Marzano, Hunt's, Compliments, Great Value…) | 1 (all) |

**Error class:** BENCHMARK LABEL PROBLEM.
**Root cause:** `["tomato","sauce","pasta"]` — `pasta` is a usage synonym forced as a conjunction. Every literal "Tomato Sauce" hits 2/3 → `rel=1`; none hit 3/3 → `P@5=P@10=0` even though every top-10 slot is the exact product typed by the user.
**Signal responsible:** incorrect relevance label.

### 14. `almond milk` — P@5 0.00 / P@10 0.10 / MRR 0.10

**NLP:** category entity `almond milk` · no filter.

| # | score | product | rel |
|---|-------|---------|-----|
| 1 | 510.7 | Almond milk (generic, no brand) | 1 |
| 2 | 443.0 | Almond Milk **Chocolate** (candy bar) | 1 |
| 3 | 443.0 | Almond Milk Bread | 1 |
| 4–9 | 443–423 | Almond milk Naturalia, Original Almond Milk, Silk Vanilla… | 1 |
| 10 | 391.1 | Creamy Original Almond Milk (Califia) | **2** |

**Error class:** BENCHMARK LABEL PROBLEM (primary) + minor ranking nuance.
**Root cause:** `["almond","milk","beverage"]` — `beverage` forced as third conjunction; most plant-milk names omit it → `rel=1`. Only category-bearing `…almond milk… beverage…` docs reach `rel=2`.
**Ranking note (not a defect):** #2–3 are chocolate bar / bread whose names contain both `almond` and `milk`; the phrase-clause `name^3.0 × phrase_boost 10.0` legitimately ranks them above purer products with sparser metadata. Not fix-worthy; it is phrase matching behaving as specified.

### 15. `extra virgin olive oil` — P@5 0.40 / P@10 0.50 / NDCG 0.58 / MRR 0.25

**NLP:** category entity `extra virgin olive oil` · no filter. Total 10,000 (capped).

| # | score | product | rel |
|---|-------|---------|-----|
| 1 | 874.7 | Extra Virgin Olive Oil (Gallo) | **0** — `DISALLOWED: vegetable oil`(!) |
| 2–3,6–7,9… | 874 | Extra virgin olive oil (Cleopatra, fiorfiore, Saporito…) | **0** |
| 4–5,8–10 | 874 | EVOO (Maison Orphée, Selection, Great Value, Acropolis, Kirkland) | **3** |

**Error class:** BENCHMARK LABEL PROBLEM (disallowed-keyword collision).
**Root cause:** `disallowed_keywords=["canola","vegetable oil"]`. The labeler checks them against `name + search_text`, and `search_text` contains the **category path**, where every olive oil inherits `… Vegetable oils, Olive oils, Extra-virgin olive oils`. So the substring `vegetable oil` zeroes most EVOO records even though the product is exactly what the user asked for. Only records with minimal category (`en:extra-virgin-olive-oils`) survive.
**Also surfaced:** query returns `total=10000` (headroom capped) because `extra virgin olive oil` matches broadly; ranking is clean (all EVOO).
**Signal responsible:** incorrect relevance label (disallowed substring vs taxonomy).

---

## NUTRITION ANALYSIS

| Query | Constraint extracted | Representation | OpenSearch clause | Judged | Result |
|---|---|---|---|---|---|
| low sugar cereal | `low_sugar: True` | binary flag (index) | `must: term attributes.flags.is_low_sugar=true` | fails (P@10 0) | **filter REAL** |
| high protein snacks | `high_protein: True` | binary flag (index) | `must: term attributes.flags.is_high_protein=true` | fails (P@10 0) | **filter REAL** |
| at least 20g protein | `protein gte 20.0 per_100g` | numeric | `must: range attributes.nutrition.proteins.per_100g gte 20.0` | passes (1.00) | **filter REAL** |
| snacks under 200 kcal | `calories lte 200.0 per_100g` | numeric | `must: range attributes.nutrition.energy-kcal.per_100g lte 200.0` | passes (1.00) | **filter REAL** |

- **`high protein` is NOT merely text.** It is a flag filter, set at index time by `SearchDocumentBuilder` as `"high protein" in categories OR proteins_100g ≥ 10.0`. Verified in returned docs: Chicken Snacks 10.1 g, Kippered snacks 21.0 g, Cashew/Fibre/Scallop snacks all flagged and numeric ≥ threshold. Same for `low sugar` (`0 ≤ sugars ≤ 5` OR category phrase): Cocca Cereal 0.0 g, Magic Spoon 0.0 g, Cereal Crackers 5.0 g.
- The two "failing" nutrition queries and the two "passing" numeric queries use **the same product pool** (e.g., Chicken Snacks is #1 in both `high protein snacks` and `snacks under 200 calories`). The entire score difference is the **benchmark keyword list**: `[snack,bar,nuts,protein]` (4 conjuncts) vs `[snack]` (1 conjunct) vs `[]` (numeric).
- Index flag statistics: `is_low_sugar` = 54,020 docs (47%), `is_high_protein` = 33,515 (29%), `is_vegan` = 140 (0.12%). The ≤ 5 g threshold is generous; 47% of the whole Canada/OFF export qualifies. Worth noting for the implementation phase (flag calibration), not a correctness bug.

**Conclusion: nutrition logic is correct end-to-end; both binary flags and numeric ranges are real filters backed by nutriment data.**

---

## CATEGORY ANALYSIS

- `frozen vegetables`: category matching is **lexical**, not structured. `frozen vegetables` hits the CATEGORIES dictionary (phrase) but no category term filter is emitted because intent is `generic_search` (category filters only activate for `intent=="category_browse"`). The engine instead relies on the text multi-match; results are correct (Bonduelle #1 = phrase in name). Failure is 100% labeler (6-keyword conjunction). Category typos/plurals verified clean elsewhere (maô / maple syrup).
- `breakfast cereal`: **no category dictionary entry** for the phrase `breakfast cereal`, so no category entity; the query proceeds as free text. `Shreddies` with category exactly `Breakfast Cereal` ranks #2 but is labeled `rel=0` because the labeler additionally demands `granola/flakes/oats`. The labeler is the entire cause of the 0.00 — the engine surfaced the exact-category product at #2.
- Neither query benefits from category-filter even when a category entity exists (generic default). **No benchmark label changes are justified yet:** the labels are wrong for reasons independent of the category investigation’s four "frozen/breakfast" queries, and are fixed by the same keyword-semantics correction.

---

## BRAND ANALYSIS

- **Extraction works.** Both queries extract `brand="compliments"` via the brands dictionary (and `soy sauce` as an ingredient). The pipeline is capable of separating brand vs product.
- **But extraction output is not used to build a brand filter.** `IntentDetector` returns `generic_search` for `"<brand> <product>"`; only `brand_search` intent (or an explicit API override of the brand param) emits a brand must-filter (`retrieval/search_engine.py:74`). So `brand match + product match` and `brand match only` are **not separated at retrieval** — both are scored purely by lexical overlap.
- Concrete proof: for `Compliments soy sauce`, the two highest-scoring docs are a **patty** (Soy Burgers, ingredients contain "soy sauce", brand Compliments, AND-clause bonus) and a **no-name** soy sauce, while the true Compliments soy sauce (`Soya sauce`) sits outside top-50. Word-level "brand match only" docs (Compliments-labeled brand pages ranks 3–7 in the cereal-bar query) pollute 5 of 10 slots.
- Damaged further by `soya`/`soy`: the true product’s name uses the `soya` spelling, so even phrase matching misses it.

**Answer to "does brand+product outrank brand-match-only?":** No. The engine has no mechanism to require the product half of the query; AND-match on the *text* rewards brands whose *ingredients/name* coincidentally contain product tokens, and fuzzy OR admits brand-only docs.

---

## GENERIC SEARCH ANALYSIS

| Query | Failure cause | Engine status |
|---|---|---|
| coffee | labeler 3-conjunct `coffee/roast/espresso` | ranking excellent (all "Coffee") |
| chips | labeler 2-conjunct `chip/crisp` | ranking excellent (all chips) |
| chocolate cookies | labeler 3-conjunct `chocolate/cookie/biscuit` | ranking excellent |
| tomato sauce | labeler 3-conjunct `tomato/sauce/pasta` | ranking excellent |
| almond milk | labeler 3-conjunct `almond/milk/beverage` (+ phrase nuance) | ranking good |
| extra virgin olive oil | labeler disallowed `vegetable oil` collides with category taxonomy | ranking excellent |

No generic query exhibits a weighted-fields, fuzziness, compound-term, or boost defect. All six are labeler semantics. The only field-weight observation: completeness (0.15) is negligible next to phrase (10.0)×name(3.0); e.g. `almond milk`'s generic unbranded name outranks branded beverages. That is by-design phrase-dominance, not a defect.

---

## ROOT CAUSE CLASSIFICATION (per query, primary)

| # | Query | Primary class |
|---|---|---|
| 1 | Compliments strawberry cereal bars | DATA COVERAGE |
| 2 | Compliments soy sauce | **RETRIEVAL BUG + NLP/query construction** |
| 3 | chips | BENCHMARK LABEL |
| 4 | coffee | BENCHMARK LABEL |
| 5 | chocolate cookies | BENCHMARK LABEL |
| 6 | vegan cookies | DATA COVERAGE |
| 7 | low sugar cereal | BENCHMARK LABEL (constraint verified real) |
| 8 | high protein snacks | BENCHMARK LABEL (constraint verified real) |
| 9 | products with at least 20g protein | EXPECTED BEHAVIOR (succeeds) |
| 10 | snacks under 200 calories | EXPECTED BEHAVIOR (succeeds) |
| 11 | frozen vegetables | BENCHMARK LABEL |
| 12 | breakfast cereal | BENCHMARK LABEL |
| 13 | tomato sauce | BENCHMARK LABEL |
| 14 | almond milk | BENCHMARK LABEL (+ minor ranking nuance) |
| 15 | extra virgin olive oil | BENCHMARK LABEL (disallowed-keyword taxonomy collision) |

---

## RECOMMENDED FIXES (only where a real defect exists; NOT implemented)

Real engine defects (3), ordered by leverage:

1. **`soya`↔`soy` tokenization gap** *(retrieval)* — High severity for brand+product queries on the Canada set.
   Fix: add `soya→soy` (plus CO/FR product-name variants) to a synonym/normalization table applied at query time for ingredient/product terms, or a filter/synonym analysis on `product_name`/`ingredients`.
2. **Brand entity never promoted to a brand filter** *(NLP / query construction)* — root enabler of "Soy Burgers beats real soy sauce" and of brand-label pollution.
   Fix: in `retrieval/search_engine.py`, when `entities["brands"]` is non-empty AND another product/ingredient/category entity exists, compile brand into a `match`-all (or boost-not-must) clause instead of leaving it breadbag in the text term.
3. **Single-token OR pollution** *(retrieval)* — `minimum_should_match=1` in the fuzzy/or clause lets brand-only labels (cereal-bar ranks 3–7), vegan-but-non-cookie items, and pizza-snack noise into top-10.
   Fix: for text terms of ≥3 tokens, raise `minimum_should_match` to ≥2 (or weight tokens by entity extraction); verify against the preserved fuzzy typo case (`peanute butter` still returns Peanut Butter first).

Do NOT fix (benchmark/data, not engine):
- **Benchmark labeler keyword semantics** — the single highest-impact "fix" for P@5/P@10, but it is a *measurement* correction: represent synonyms as OR-groups (`chip|crisp`, `coffee|roast|espresso`, `chocolate|cookie|biscuit`, `almond|milk|beverage`, `soya|soy|sauce`, `cereal|granola|oats|flakes`, `frozen|vegetable|peas|corn|broccoli|blend`, `tomato|sauce|pasta`), and for `vegan cookies` / `low sugar` / `high protein` require only the *product* keyword + the flag.
- **`extra virgin olive oil` disallowed-keyword collision** — remove `vegetable oil` from that query's `disallowed_keywords` (or match against `product_name` only).
- **Data coverage** — `Compliments strawberry cereal bars` (1 product) and `vegan cookies` (2 flagged cookies) cannot score higher; re-baseline these queries with the fixed labeler and accept the ceiling.
- **`is_vegan` low recall (140/114,453)** and **`is_low_sugar` permissiveness (54,020)** — flag calibration is an index-time data-quality decision for a later phase, not a retrieval bug.
- **`chips` in the BRANDS dictionary** — dictionary noise, benign today.

---

## PRIORITY TABLE

| Issue | Type | Severity | Engineering Fix? | Priority |
|---|---|---|---|---|
| `soya`/`soy` tokenization gap (Compliments soy sauce misses true product) | Retrieval bug | High | Yes (synonym/normalization) | P0 |
| Brand entity not compiled into brand filter (brand+product queries) | NLP/query-construction bug | High | Yes (brand must clause) | P0 |
| Single-token OR pollution (`minimum_should_match=1`) | Retrieval bug | Medium | Yes (≥2 for 3+ token terms) | P1 |
| Benchmark keyword lists treat synonyms as conjunctions (10 queries) | Benchmark label | High (distortion) | No — fix measurement | P0 (labels) |
| EVOO: `vegetable oil` disallowed collides with category taxonomy | Benchmark label | Medium | No — fix measurement | P1 (labels) |
| Data coverage: 1 Compliments cereal bar; 2 vegan cookies | Data limitation | Low | No | P2 |
| Flag calibration `is_low_sugar` 47% / `is_vegan` 0.12% | Data limitation | Low | No (later phase) | P2 |
| `chips` present in BRANDS dictionary | NLP data noise | Trivial | Optional cleanup | P3 |

---

## TALLY

```
REAL ENGINE BUGS : 3     (soya/soy tokenization; brand-filter promotion gap; single-token OR pollution)
NLP BUGS         : 1     (brand entity not lifted to a brand filter — the "query construction" half of the brand issue)
RETRIEVAL BUGS   : 2     (soya/soy gap; minimum_should_match OR pollution)
DATA LIMITATIONS : 3     (Compliments cereal bars=1 product; vegan cookies=2 flagged; flag-coverage calibration)
BENCHMARK/LABEL ISSUES : 10  (chips, coffee, chocolate cookies, low sugar cereal, high protein snacks,
                              frozen vegetables, breakfast cereal, tomato sauce, almond milk, extra virgin olive oil)
EXPECTED BEHAVIOR: 2     (products with at least 20g protein; snacks under 200 calories — correct and passing)
```

**Bottom line:** The engine's ranking, constraint engine (nutrition binary flags **and** numeric ranges), and generic retrieval are functioning correctly; 10 of 15 analyzed queries fail the benchmark because the labeler models synonyms/example-terms as mandatory conjunctions, 2 are hard data-coverage ceilings, and 1 (Compliments soy sauce) exposes 3 real-but-small defects worth fixing during the implementation phase.