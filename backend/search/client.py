from opensearchpy import OpenSearch
from config.settings import settings


def get_client() -> OpenSearch:
    return OpenSearch(
        hosts=settings.opensearch_hosts,
        use_ssl=settings.opensearch_use_ssl,
    )
