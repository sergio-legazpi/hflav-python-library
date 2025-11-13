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
from source.source_interface import SourceInterface


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
            results.append(
                Record(
                    id=hit.get("id"),
                    doi=hit.get("doi"),
                    title=hit.get("metadata", {}).get("title"),
                    created=hit.get("created"),
                    updated=hit.get("updated"),
                    links=hit.get("links", {}),
                    files=[
                        File(
                            name=file.get("key"),
                            download_url=file.get("links", {}).get("self"),
                        )
                        for file in hit.get("files", [])
                    ],
                )
            )

        return results

    def get_correct_template_by_date(
        self, date: Optional[datetime.date] = None
    ) -> Dict[str, Any]:
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

            all_versions.append(
                Template(
                    title=version.get("metadata", {}).get("title"),
                    created=version.get("created"),
                    updated=version.get("updated"),
                    version=version.get("metadata", {}).get("version"),
                    jsons=[
                        item
                        for item in version.get("files", [])
                        if item["key"].endswith(".json")
                    ],
                )
            )

        return all_versions

    def get_record(self, recid: int) -> Dict[str, Any]:
        """Fetch a single record by id (record id as shown in Zenodo URL)."""
        url = f"{self.DEFAULT_BASE}/records/{recid}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_file_by_id(
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

        files = record.get("files") or []
        if not files:
            raise ValueError("Record contains no files")

        chosen = None
        if filename:
            for f in files:
                if f.get("key") == filename or f.get("filename") == filename:
                    chosen = f
                    break
        if not chosen:
            chosen = files[0]

        # file links: try 'links'->'download' or 'links'->'self'
        links = chosen.get("links", {})
        url = links.get("download") or links.get("self") or chosen.get("url")
        if not url:
            raise ValueError("No download link found for file")

        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()

        dest_is_dir = dest_path and os.path.isdir(dest_path)
        if dest_path is None or dest_is_dir:
            filename_on_disk = (
                chosen.get("key")
                or chosen.get("filename")
                or f"record_{record.get('id')}_file"
            )
            out_path = os.path.join(dest_path or os.getcwd(), filename_on_disk)
        else:
            out_path = dest_path

        with open(out_path, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)

        return out_path
