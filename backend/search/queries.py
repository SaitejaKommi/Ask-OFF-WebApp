from .ranking import RankingConfig


def build_search_query(
    q: str,
    ranking_config: RankingConfig,
    size: int = 20,
    from_: int = 0,
) -> dict:
    fields = [
        f"{field}^{boost}" for field, boost in ranking_config.field_boosts.items()
    ]
    return {
        "size": size,
        "from": from_,
        "query": {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": q,
                            "fields": fields,
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                            "operator": "or",
                        }
                    }
                ],
            }
        },
    }


def build_autocomplete_query(q: str, size: int = 5) -> dict:
    return {
        "size": size,
        "query": {
            "multi_match": {
                "query": q,
                "fields": [
                    "product_name_clean.autocomplete",
                    "search_text.autocomplete",
                ],
                "type": "bool_prefix",
            }
        },
    }


def build_product_query(code: str) -> dict:
    return {"query": {"term": {"code": code}}}


def build_brand_query(brand: str, size: int = 20) -> dict:
    return {
        "size": size,
        "query": {"match": {"brands_clean": {"query": brand, "operator": "and"}}},
    }


def build_category_query(category: str, size: int = 20) -> dict:
    return {
        "size": size,
        "query": {
            "match": {"categories_clean": {"query": category, "operator": "and"}}
        },
    }
