from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASKOFF_", env_file=".env")

    opensearch_hosts: list[str] = ["localhost:9200"]
    opensearch_index: str = "askoff_products"
    opensearch_use_ssl: bool = False
    opensearch_username: Optional[str] = None
    opensearch_password: Optional[str] = None
    opensearch_verify_certs: bool = False

    raw_data_path: Path = Path("data/raw/normalized.parquet")
    processed_dir: Path = Path("data/processed")
    dataset_url: str = ""

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    pipeline_batch_size: int = 1000

    cors_origins: list[str] = ["*"]
    completeness_weight: float = 0.15


settings = Settings()
