from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from hflav_zenodo.models.models import File, Record, Template


class SourceInterface(ABC):
    """Abstract interface for source clients used by HFLAV.

    This defines the public contract implemented by `ZenodoClient` in
    `source_zenodo.py`. Implementations must provide the methods below and
    follow the documented input/output shapes (they generally return JSON-like
    dicts or file paths).
    """

    @abstractmethod
    def get_records_by_name(
        self, query: Optional[str] = None, size: int = 10, page: int = 1
    ) -> List[Record]:
        """Search records and return the JSON-decoded response.

        Args:
                query: optional free-text query
                size: number of results to return
                page: page number

        Returns:
                A list of records.
        """

    @abstractmethod
    def get_correct_template_by_date(self, date: Optional[datetime] = None) -> Template:
        """Search the correct template version to the date given.

        Args:
                date: date to search the correct template for

        Returns:
                A Template instance.
        """

    @abstractmethod
    def get_record(self, recid: int) -> Record:
        """Fetch a single record by id (record id as shown in Zenodo URL).
        Args:
                recid: integer id of the record

        Returns:
                A Record instance.
        """

    @abstractmethod
    def download_file_by_id_and_filename(
        self,
        id: int,
        filename: Optional[str] = None,
        dest_path: Optional[str] = None,
    ) -> str:
        """Download a file referenced by a record and return the saved path.

        Args:
                id: integer id of the record
                filename: optional filename/key to select a specific file in the record
                dest_path: optional destination directory or full path

        Returns:
                The filesystem path to the saved file.
        """
