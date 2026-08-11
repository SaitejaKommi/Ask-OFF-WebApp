import logging

logger = logging.getLogger(__name__)

BRANDS = set()
CATEGORIES = set()
INGREDIENTS = set()

# Allergens and nutrition and sustainability are usually static sets
ALLERGENS = {
    "gluten", "lactose", "peanuts", "nuts", "soy", "eggs", "dairy", "milk", "wheat"
}

SUSTAINABILITY_LABELS = {
    "organic", "bio", "fair trade", "rainforest alliance", "non-gmo", "green"
}

NUTRITION = {
    "protein", "sugar", "sodium", "salt", "fat", "carbs", "carbohydrates", "energy", "calories"
}

def load_dynamic_dictionaries():
    logger.info("Dynamically loading entity dictionaries from OpenSearch...")
    try:
        from search.client import get_client
        from config.settings import settings
        
        client = get_client()
        if not client.indices.exists(index=settings.opensearch_index):
            logger.warning("Index does not exist. Cannot load dynamic dictionaries.")
            return

        body = {
            "size": 0,
            "aggs": {
                "brands": {"terms": {"field": "brand.keyword", "size": 10000}},
                "categories": {"terms": {"field": "category.keyword", "size": 10000}},
                "ingredients": {"terms": {"field": "ingredients.keyword", "size": 10000}}
            }
        }
        res = client.search(index=settings.opensearch_index, body=body)
        
        aggs = res.get("aggregations", {})
        
        if "brands" in aggs:
            for b in aggs["brands"]["buckets"]:
                for part in b["key"].split(","):
                    if part.strip(): BRANDS.add(part.strip().lower())
        if "categories" in aggs:
            for c in aggs["categories"]["buckets"]:
                for part in c["key"].split(","):
                    if part.strip(): CATEGORIES.add(part.strip().lower())
        if "ingredients" in aggs:
            for i in aggs["ingredients"]["buckets"]:
                for part in i["key"].split(","):
                    if part.strip(): INGREDIENTS.add(part.strip().lower())
            
        logger.info(f"Loaded {len(BRANDS)} brands, {len(CATEGORIES)} categories, {len(INGREDIENTS)} ingredients.")
    except Exception as e:
        logger.error(f"Failed to load dynamic dictionaries: {e}")
