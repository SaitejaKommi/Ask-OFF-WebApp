from typing import List, Dict, Any, Set
from query.dictionaries import BRANDS, CATEGORIES, INGREDIENTS, ALLERGENS, SUSTAINABILITY_LABELS, NUTRITION
from query.tokenizer import QueryTokenizer

# Simple country and region dictionary for geographical matching
COUNTRIES = {"canada", "usa", "us", "uk", "france", "germany", "vermont"}

class EntityExtractor:
    @staticmethod
    def extract(normalized_query: str, intent: str = "generic_search") -> Dict[str, List[Dict[str, Any]]]:
        tokens = QueryTokenizer.tokenize(normalized_query)
        ngrams = QueryTokenizer.generate_ngrams(tokens, max_n=4)
        
        entities: Dict[str, List[Dict[str, Any]]] = {
            "products": [],
            "brands": [],
            "categories": [],
            "ingredients": [],
            "nutrition": [],
            "allergens": [],
            "sustainability_labels": [],
            "countries": []
        }
        
        import re
        if intent == "brand_search":
            explicit_brand = None
            if m := re.search(r"\bshow me (.+) products\b", normalized_query):
                explicit_brand = m.group(1).strip()
            elif m := re.search(r"\bproducts by (.+)\b", normalized_query):
                explicit_brand = m.group(1).strip()
            elif m := re.search(r"\b(?:brand|by brand) (.+)\b", normalized_query):
                explicit_brand = m.group(1).strip()
            
            if explicit_brand:
                entities["brands"].append({
                    "value": explicit_brand,
                    "explanation": f"Explicitly extracted '{explicit_brand}' from intent pattern"
                })
                # if it's explicitly extracted, we don't need to try and find it again in n-grams.
                # but we will let n-grams run for other entities.
                
        matched_spans: Set[int] = set()
        
        for ngram in ngrams:
            ngram_tokens = ngram.split()
            n = len(ngram_tokens)
            
            start_idx = -1
            for i in range(len(tokens) - n + 1):
                if tokens[i:i+n] == ngram_tokens:
                    span_indices = set(range(i, i + n))
                    if not span_indices.intersection(matched_spans):
                        start_idx = i
                        break
            
            if start_idx == -1:
                continue
                
            matched = False
            
            if ngram in BRANDS:
                entities["brands"].append({
                    "value": ngram,
                    "explanation": f"Matched '{ngram}' in the brands lookup dictionary"
                })
                matched = True
            elif ngram in CATEGORIES:
                entities["categories"].append({
                    "value": ngram,
                    "explanation": f"Matched '{ngram}' in the categories lookup dictionary"
                })
                matched = True
            elif ngram in INGREDIENTS:
                entities["ingredients"].append({
                    "value": ngram,
                    "explanation": f"Matched '{ngram}' in the ingredients lookup dictionary"
                })
                matched = True
            elif ngram in ALLERGENS:
                entities["allergens"].append({
                    "value": ngram,
                    "explanation": f"Matched '{ngram}' in the allergens lookup dictionary"
                })
                matched = True
            elif ngram in SUSTAINABILITY_LABELS:
                entities["sustainability_labels"].append({
                    "value": ngram,
                    "explanation": f"Matched '{ngram}' in the sustainability labels lookup dictionary"
                })
                matched = True
            elif ngram in NUTRITION:
                entities["nutrition"].append({
                    "value": ngram,
                    "explanation": f"Matched '{ngram}' in the nutrition lookup dictionary"
                })
                matched = True
            elif ngram in COUNTRIES:
                entities["countries"].append({
                    "value": ngram,
                    "explanation": f"Matched '{ngram}' as a recognized country or region"
                })
                matched = True
                
            if matched:
                matched_spans.update(range(start_idx, start_idx + n))
                
        return entities
