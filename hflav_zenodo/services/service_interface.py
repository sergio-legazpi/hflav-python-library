"""Service layer interface.

Defines the contract that concrete service implementations (e.g. `Services`) must
fulfill. This abstraction allows easier testing (mocking) and future alternative
implementations (remote service, cached service, etc.).
"""

from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Optional, List

from hflav_zenodo.filters.base_query import BaseQuery
from hflav_zenodo.models.models import Record


class ServiceInterface(ABC):
    """Abstract interface for service operations.

    Methods are intentionally narrow and side-effect free except for
    `search_and_load_data_file` which performs interactive selection.
    """

    @abstractmethod
    def search_records_by_name(self, query: BaseQuery) -> List[Record]:
        """Search records by textual query.

        Returns a list of `Record` objects; should never raise on data access
        errors but instead return an empty list or handle logging internally.
        """
        raise NotImplementedError

    @abstractmethod
    def search_and_load_data_file(self, query: BaseQuery) -> SimpleNamespace:
        """Interactive helper which searches records and lets the user pick a file.

        Implementations may request input() from stdin; returned object is a dynamic
        namespace representation of the chosen JSON data.
        """
        raise NotImplementedError

    @abstractmethod
    def load_data_file(
        self, record_id: int, filename: str, dest_path: Optional[str] = None
    ) -> SimpleNamespace:
        """Load a specific file from a record by id and filename.

        Responsible for resolving the correct template version, downloading the file
        and converting it into a structured namespace.
        """
        raise NotImplementedError
