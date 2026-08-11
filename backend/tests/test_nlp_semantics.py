import pytest
from query.pipeline import SearchQueryPipeline
from query import dictionaries
import query.dictionaries

# Mock dictionaries so entity extraction works predictably for tests
dictionaries.BRANDS.update({"kirkland", "nature valley"})
dictionaries.CATEGORIES.update({"snacks", "cookies", "chips", "cereal", "chocolate", "meals"})
dictionaries.INGREDIENTS.update({"sugar", "peanut butter", "milk", "palm oil", "chocolate"})

def test_low_sugar_constraint_does_not_leak_into_text():
    sq = SearchQueryPipeline.process("low sugar peanut butter")
    assert sq.filters.get("low_sugar") is True
    assert "sugar" not in sq.text_term
    assert "low" not in sq.text_term
    assert "peanut butter" in sq.text_term

def test_high_protein_constraint_does_not_leak_into_text():
    sq = SearchQueryPipeline.process("high protein snacks")
    assert sq.filters.get("high_protein") is True
    assert "protein" not in sq.text_term
    assert "high" not in sq.text_term
    assert "snacks" in sq.text_term

def test_low_sodium_constraint_does_not_leak_into_text():
    sq = SearchQueryPipeline.process("low sodium chips")
    assert sq.filters.get("low_sodium") is True
    assert "sodium" not in sq.text_term
    assert "low" not in sq.text_term
    assert "chips" in sq.text_term

def test_gluten_free_constraint_does_not_leak_into_text():
    sq = SearchQueryPipeline.process("gluten free cookies")
    assert sq.filters.get("gluten_free") is True
    assert "gluten" not in sq.text_term
    assert "free" not in sq.text_term
    assert "cookies" in sq.text_term

def test_palm_oil_free_constraint_does_not_leak_into_text():
    sq = SearchQueryPipeline.process("palm oil free peanut butter")
    assert sq.filters.get("palm_oil") is False
    assert "palm" not in sq.text_term
    assert "oil" not in sq.text_term
    assert "free" not in sq.text_term
    assert "peanut butter" in sq.text_term

def test_vegan_constraint_does_not_leak_into_text():
    sq = SearchQueryPipeline.process("vegan chocolate")
    assert sq.filters.get("vegan") is True
    assert "vegan" not in sq.text_term
    assert "chocolate" in sq.text_term

def test_plain_sugar_query_remains_sugar():
    sq = SearchQueryPipeline.process("sugar")
    assert sq.text_term == "sugar"
    assert sq.filters.get("low_sugar") is None

def test_sugar_cookie_query_remains_valid():
    sq = SearchQueryPipeline.process("sugar cookies")
    assert "sugar" in sq.text_term
    assert "cookies" in sq.text_term
    assert sq.filters.get("low_sugar") is None

def test_explicit_brand_query_filters_brand():
    sq = SearchQueryPipeline.process("by brand kirkland")
    assert sq.intent == "brand_search"
    assert len(sq.entities.get("brands", [])) > 0
    assert sq.entities["brands"][0]["value"] == "kirkland"

def test_general_brand_query_does_not_overfilter():
    sq = SearchQueryPipeline.process("kirkland peanut butter")
    assert sq.intent == "generic_search"
    assert len(sq.entities.get("brands", [])) > 0
    assert sq.entities["brands"][0]["value"] == "kirkland"
    assert "kirkland" in sq.text_term
    # In SearchEngine, because intent is generic_search, it will NOT become a MUST filter,
    # but the pipeline should still extract it as an entity.
