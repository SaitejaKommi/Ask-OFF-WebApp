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
            "code": {"type": "keyword"},
            "product_name": {"type": "text", "analyzer": "standard"},
            "product_name_clean": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                    }
                },
            },
            "brands": {"type": "text", "analyzer": "standard"},
            "brands_clean": {"type": "text", "analyzer": "standard"},
            "categories": {"type": "text", "analyzer": "standard"},
            "categories_clean": {"type": "text", "analyzer": "standard"},
            "ingredients_text": {"type": "text", "analyzer": "standard"},
            "ingredients_clean": {"type": "text", "analyzer": "standard"},
            "nutriments": {"type": "object", "enabled": False},
            "nutriscore_grade": {"type": "keyword"},
            "nova_group": {"type": "integer"},
            "ecoscore_grade": {"type": "keyword"},
            "completeness": {"type": "float"},
            "search_text": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                    }
                },
            },
            "semantic_document": {"type": "text", "analyzer": "standard"},
        }
    },
}
