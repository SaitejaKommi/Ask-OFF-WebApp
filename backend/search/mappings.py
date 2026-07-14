PRODUCT_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "autocomplete_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "autocomplete_filter"],
                }
            },
            "filter": {
                "autocomplete_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                }
            },
        },
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "core_product_id": {"type": "keyword"},
            "variant_id": {"type": "keyword"},
            "product_name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "standard",
                    }
                },
            },
            "brand": {"type": "text", "analyzer": "standard"},
            "category": {"type": "text", "analyzer": "standard"},
            "ingredients": {"type": "text", "analyzer": "standard"},
            "nutrition": {"type": "object", "enabled": False},
            "flags": {
                "properties": {
                    "is_organic": {"type": "boolean"},
                    "is_vegan": {"type": "boolean"},
                    "is_vegetarian": {"type": "boolean"},
                }
            },
            "metadata": {
                "properties": {
                    "nutriscore_grade": {"type": "keyword"},
                    "nova_group": {"type": "integer"},
                    "ecoscore_grade": {"type": "keyword"},
                    "completeness": {"type": "float"},
                }
            },
            "search_text": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "standard",
                    }
                },
            },
            "semantic_document": {"type": "text", "analyzer": "standard"},
        }
    },
}

