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
            "dataset_id": {"type": "keyword"},
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
            "brand": {
                "type": "text", 
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256}
                }
            },
            "category": {
                "type": "text", 
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256}
                }
            },
            "ingredients": {
                "type": "text", 
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256}
                }
            },
            "attributes": {"type": "object", "dynamic": True},
            "metadata": {"type": "object", "dynamic": True},
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
