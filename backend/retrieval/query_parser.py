import re


class QueryParser:
    @staticmethod
    def parse(query: str) -> str:
        if not query:
            return ""
        cleaned = re.sub(r"[^\w\s\-\.]", "", query)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned
