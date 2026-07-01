import json
import logging
import math

from opensearchpy import OpenSearch, helpers

from config.settings import settings
from .client import get_client
from .mappings import PRODUCT_INDEX_MAPPING

logger = logging.getLogger(__name__)


def _sanitize(obj: object) -> object:
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


class _NanSafeJSONEncoder(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, float) and math.isnan(obj):
            return None
        return super().default(obj)


def ensure_index(client: OpenSearch) -> None:
    index_name = settings.opensearch_index
    if client.indices.exists(index=index_name):
        logger.info("Index '%s' already exists", index_name)
        return
    client.indices.create(index=index_name, body=PRODUCT_INDEX_MAPPING)
    logger.info("Created index '%s'", index_name)


def delete_index(client: OpenSearch) -> None:
    index_name = settings.opensearch_index
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
        logger.info("Deleted index '%s'", index_name)


def index_products(products: list[dict]) -> int:
    client = get_client()
    ensure_index(client)

    actions = [
        {
            "_index": settings.opensearch_index,
            "_id": p["code"],
            "_source": _sanitize(p),
        }
        for p in products
    ]

    success, errors = helpers.bulk(
        client,
        actions,
        raise_on_error=False,
    )
    if errors:
        logger.error("Indexing errors (showing first 5): %s", errors[:5])
        for err in errors[:5]:
            detail = err.get("index", {}).get("error", {})
            logger.error("  Reason: %s", detail.get("reason", "unknown"))

    logger.info("Indexed %d products (%d errors)", success, len(errors))
    return success
