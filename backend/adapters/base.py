from abc import ABC, abstractmethod
from typing import Iterable
from models.raw_product import RawProduct

class BaseAdapter(ABC):
    @abstractmethod
    def extract_raw_products(self, limit: int | None = None) -> Iterable[RawProduct]:
        pass
