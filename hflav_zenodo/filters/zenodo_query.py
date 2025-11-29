from typing import Any, Dict, List, Optional

from hflav_zenodo.filters.base_query import BaseQuery
from hflav_zenodo.filters.search_filters import Filter


# Main Query
class ZenodoQuery(BaseQuery):
    DEFAULT_COMMUNITY = "hflav"

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

        params["sort"] = self.sort
        return params

    def __str__(self) -> str:
        return self.build_query_string()
