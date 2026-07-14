import logging
from pathlib import Path
from typing import Optional, Type

from adapters.base import BaseAdapter
from adapters.off_adapter import OFFAdapter
from builders.search_document_builder import SearchDocumentBuilder
from pipeline.load import write_normalized_parquet
from search.indexer import index_products
from models.search_document import SearchDocument

logger = logging.getLogger(__name__)


def run_pipeline(
    csv_path: str | None = None,
    adapter_class: Type[BaseAdapter] = OFFAdapter,
    builder: SearchDocumentBuilder = SearchDocumentBuilder(),
    limit: Optional[int] = None,
    index_to_opensearch: bool = True,
) -> Path:
    logger.info("Initializing adapter and builder...")
    adapter = adapter_class(csv_path) if adapter_class == OFFAdapter else adapter_class()

    logger.info("Streaming and transforming raw products...")
    search_docs: list[SearchDocument] = []
    batch: list[SearchDocument] = []
    total_indexed = 0

    for raw_product in adapter.extract_raw_products(limit=limit):
        doc = builder.build(raw_product)
        search_docs.append(doc)

        if index_to_opensearch:
            batch.append(doc)
            if len(batch) >= 1000:
                total_indexed += index_products(batch)
                batch = []

    if index_to_opensearch and batch:
        total_indexed += index_products(batch)

    logger.info("Indexed %d search documents to OpenSearch", total_indexed)

    output_path = write_normalized_parquet(search_docs)
    logger.info("Pipeline complete. Output: %s", output_path)
    return output_path

