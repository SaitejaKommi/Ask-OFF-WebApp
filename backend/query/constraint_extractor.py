import re
from typing import Dict, Any, List

class ConstraintExtractor:
    @staticmethod
    def extract(normalized_query: str) -> Dict[str, Any]:
        filters = {
            "organic": None,
            "vegan": None,
            "vegetarian": None,
            "palm_oil": None,
            "high_protein": None,
            "low_sugar": None,
            "low_sodium": None,
            "gluten_free": None,
            "lactose_free": None
        }
        
        cleaned_query = normalized_query
        explanations = []
        
        patterns = [
            (r"\b(?:organic|bio)\b", "organic", True, "Matched 'organic' or 'bio' keyword indicating organic certification"),
            (r"\bvegan\b", "vegan", True, "Matched 'vegan' keyword indicating vegan requirement"),
            (r"\b(?:vegetarian|veggie)\b", "vegetarian", True, "Matched 'vegetarian' or 'veggie' keyword indicating vegetarian requirement"),
            (r"\b(?:no[- ]palm[- ]oil|palm[- ]oil[- ]free|without[- ]palm[- ]oil|free[- ]of[- ]palm[- ]oil)\b", "palm_oil", False, "Matched phrase indicating palm oil exclusion"),
            (r"\b(?:palm[- ]oil)\b", "palm_oil", True, "Matched 'palm oil' keyword"),
            (r"\b(?:high[- ]protein|protein[- ]rich|rich[- ]in[- ]protein|extra[- ]protein)\b", "high_protein", True, "Matched phrase indicating high protein requirement"),
            (r"\b(?:low[- ]sugar|sugar[- ]free|zero[- ]sugar|no[- ]sugar|without[- ]sugar|less[- ]sugar)\b", "low_sugar", True, "Matched phrase indicating low or zero sugar requirement"),
            (r"\b(?:low[- ]sodium|sodium[- ]free|salt[- ]free|no[- ]salt|low[- ]salt|no[- ]sodium|without[- ]sodium|less[- ]sodium)\b", "low_sodium", True, "Matched phrase indicating low or zero sodium/salt requirement"),
            (r"\b(?:gluten[- ]free|no[- ]gluten|without[- ]gluten|free[- ]of[- ]gluten)\b", "gluten_free", True, "Matched phrase indicating gluten-free requirement"),
            (r"\b(?:lactose[- ]free|dairy[- ]free|no[- ]lactose|without[- ]lactose|free[- ]of[- ]lactose)\b", "lactose_free", True, "Matched phrase indicating lactose-free requirement")
        ]

        for pattern, key, value, explanation in patterns:
            if filters[key] is not None:
                continue
            if re.search(pattern, cleaned_query):
                filters[key] = value
                explanations.append({"field": key, "explanation": explanation})
                cleaned_query = re.sub(pattern, "", cleaned_query)
        
        cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()
            
        return {
            "filters": filters,
            "explanations": explanations,
            "cleaned_query": cleaned_query
        }
