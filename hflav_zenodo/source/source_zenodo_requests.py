"""Zenodo client utilities for HFLAV data.

This module provides a small wrapper around the Zenodo REST API to search
and download records related to HFLAV. It's intentionally small and
dependency-light (only `requests`).
"""

from typing import Optional, Dict, Any, List
import requests
import os
from datetime import datetime

from hflav_zenodo.models.models import File, Record, Template
from hflav_zenodo.source.source_interface import SourceInterface


class SourceZenodoRequest(SourceInterface):
    """Simple Zenodo API client.

    Basic contract
    - Inputs: query strings, community name, record id
    - Outputs: parsed JSON from Zenodo or downloaded file path
    - Error modes: raises requests.exceptions on network errors; ValueError
      on missing content.
    """

    DEFAULT_BASE = "https://zenodo.org/api"
    DEFAULT_COMMUNITY = "hflav"
    CONCEPT_ID_TEMPLATE = 12087575  # Template record for HFLAV data files

    def get_records_by_name(
        self,
        query: Optional[str] = None,
        size: int = 10,
        page: int = 1,
    ) -> Dict[str, Any]:
        search_url = f"{self.DEFAULT_BASE}/records"
        params = {
            "communities": self.DEFAULT_COMMUNITY,
            "q": query,
            "size": size,
            "page": page,
        }

        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = []
        for hit in data.get("hits", {}).get("hits", []):
            results.append(Record(**hit))

        return results

    def _get_all_template_versions(self) -> List[Template]:
        record_url = f"{self.DEFAULT_BASE}/records/{self.CONCEPT_ID_TEMPLATE}"
        response = requests.get(record_url, timeout=30)
        response.raise_for_status()
        record_data = response.json()

        # Get all versions
        versions_url = record_data.get("links", {}).get("versions")
        if not versions_url:
            raise ValueError(
                f"No versions link found for record {self.CONCEPT_ID_TEMPLATE}"
            )

        versions_response = requests.get(versions_url, timeout=30)
        versions_response.raise_for_status()
        versions_data = versions_response.json()

        all_versions = []
        for version in versions_data.get("hits", {}).get("hits", []):

            all_versions.append(Template(**version))

        return all_versions

    def get_correct_template_by_date(self, date: Optional[datetime] = None) -> Template:
        templates = self._get_all_template_versions()
        if date is None:
            # Return the latest version
            latest_template = max(templates, key=lambda t: t.created)
            return latest_template
        else:
            # Find the latest template before or on the given date
            valid_templates = [
                t for t in templates if t.created.timestamp() <= date.timestamp()
            ]
            if not valid_templates:
                raise ValueError(f"No template versions found before date {date}")
            correct_template = max(valid_templates, key=lambda t: t.created)
            return correct_template

    def get_record(self, recid: int) -> Record:
        """Fetch a single record by id (record id as shown in Zenodo URL)."""
        url = f"{self.DEFAULT_BASE}/records/{recid}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return Record(**data)

    def download_file_by_id_and_filename(
        self,
        id: int,
        filename: Optional[str] = None,
        dest_path: Optional[str] = None,
    ) -> str:
        """Download a file from a record.

        - record_or_id: either the record JSON (dict) or the record id (int)
        - filename: if provided, choose that file from the record.files list
        - dest_path: directory or full filename to save; if None uses cwd

        Returns the path to the saved file.
        """
        if isinstance(id, int):
            record = self.get_record(id)
        else:
            raise ValueError("record_or_id must be an int or a record dict")

        chosen = record.get_file_by_name(filename) if filename else record.files[0]
        url = chosen.download_url
        if not url:
            raise ValueError("No download link found for file")

        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()

        dest_is_dir = dest_path and os.path.isdir(dest_path)
        if dest_path is None or dest_is_dir:
            filename_on_disk = chosen.name or f"record_{record.id}_file"
            out_path = os.path.join(dest_path or os.getcwd(), filename_on_disk)
        else:
            out_path = dest_path

        with open(out_path, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)

        return out_path
