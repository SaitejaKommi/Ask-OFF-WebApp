from typing import Dict, Any

class IntentDetector:
    @staticmethod
    def detect(query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        
        intent = {
            "type": "generic",
            "extracted_term": query
        }
        
        if query_lower.startswith("brand:"):
            intent["type"] = "brand"
            intent["extracted_term"] = query[6:].strip()
        elif query_lower.startswith("category:"):
            intent["type"] = "category"
            intent["extracted_term"] = query[9:].strip()
        elif query_lower.startswith("ingredient:"):
            intent["type"] = "ingredient"
            intent["extracted_term"] = query[11:].strip()
            
        return intent
