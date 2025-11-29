from abc import ABC
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from hflav_zenodo.filters.search_filters import Filter


class BaseQuery(ABC):
    """Base class for query builders."""

    def __init__(
        self,
        filter: "Filter",
        sort: str,
        size: int = 10,
        page: int = 1,
    ):
        self.filter = filter
        self.sort = sort
        self.size = size
        self.page = page

    def build_params(self) -> Dict[str, Any]:
        """Build the query parameters for API requests.

        Returns:
            A dictionary of query parameters.
        """
        raise NotImplementedError

    def build_query_string(self) -> str:
        """Build the query string for API requests.

        Returns:
            A string representing the query.
        """
        raise NotImplementedError
