from typing import Any, Dict, List, Optional

from hflav_zenodo.filters.base_query import BaseQuery
from hflav_zenodo.filters.search_filters import Filter


# Main Query
class ZenodoQuery(BaseQuery):
    DEFAULT_COMMUNITY = "hflav"

    def __init__(
        self,
        filter: Optional[Filter] = None,
        orders: List[str] = None,
        size: int = 10,
        page: int = 1,
    ):
        self.filter = filter
        self.orders = orders or []
        self.size = size
        self.page = page

    def build_query_string(self) -> str:
        parts = []

        if self.filter:
            parts.append(self.filter.build_query())

        return " ".join(parts) if parts else ""

    def build_params(self) -> Dict[str, Any]:
        params = {
            "communities": self.DEFAULT_COMMUNITY,
            "size": self.size,
            "page": self.page,
        }

        query_string = self.build_query_string()
        if query_string:
            params["q"] = query_string

        if self.orders:
            params["sort"] = ",".join(self.orders)
        else:
            params["sort"] = "newest"

        return params
