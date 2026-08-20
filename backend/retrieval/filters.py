from typing import Any, Dict


class FiltersManager:
    @staticmethod
    def build_filters(
        raw_filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Accepts a generic key-value filter dictionary and returns
        a cleaned version with None values removed.
        """
        return {k: v for k, v in raw_filters.items() if v is not None}
