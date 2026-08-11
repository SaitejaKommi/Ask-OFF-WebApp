import re

class QueryNormalizer:
    @staticmethod
    def normalize(query: str) -> str:
        if not query:
            return ""
        normalized = query.lower()
        # Remove punctuation except hyphens and spaces
        normalized = re.sub(r"[^\w\s\-]", "", normalized)
        # Collapse multiple spaces and trim edges
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized
