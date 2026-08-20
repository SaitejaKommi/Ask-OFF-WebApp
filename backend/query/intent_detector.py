import re


class IntentDetector:
    @staticmethod
    def detect(normalized_query: str) -> str:
        brand_patterns = [
            r"\b(?:brand|by brand|brands)\b",
            r"\bshow me (?:.+) products\b",
            r"\bproducts by (?:.+)\b"
        ]
        if any(re.search(p, normalized_query) for p in brand_patterns):
            return "brand_search"

        if re.search(r"\b(?:category|categories|under category|in category)\b", normalized_query):
            return "category_browse"

        if re.search(r"\b(?:ingredient|ingredients|made of|contains)\b", normalized_query):
            return "ingredient_search"

        return "generic_search"
