from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASKOFF_", env_file=".env")

    opensearch_hosts: list[str] = ["localhost:9200"]
    opensearch_index: str = "askoff_products"
    opensearch_use_ssl: bool = False

    raw_data_path: Path = Path("data/raw/open_food_facts_canada_all_columns.csv")
    processed_dir: Path = Path("data/processed")
    dataset_url: str = ""

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    pipeline_batch_size: int = 5000


settings = Settings()
