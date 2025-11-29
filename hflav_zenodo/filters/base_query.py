from abc import ABC
from typing import Any, Dict


class BaseQuery(ABC):
    """Base class for query builders."""

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
