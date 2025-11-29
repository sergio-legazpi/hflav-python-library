from typing import Optional, Dict, Any, List
import requests
import os
from datetime import datetime

from hflav_zenodo.exceptions.source_exceptions import (
    DataAccessException,
    DataNotFoundException,
)
from hflav_zenodo.filters.base_query import BaseQuery
from hflav_zenodo.models.models import File, Record, Template
from hflav_zenodo.source.source_interface import SourceInterface


class SourceZenodoRequest(SourceInterface):

    DEFAULT_BASE = "https://zenodo.org/api"
    CONCEPT_ID_TEMPLATE = 12087575  # Template record for HFLAV data files

    def get_records_by_name(self, query: BaseQuery) -> Dict[str, Any]:
        search_url = f"{self.DEFAULT_BASE}/records"
        params = query.build_params()

        response = requests.get(search_url, params=params, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise DataAccessException("Failed to get records by name", details=str(e))
        data = response.json()

        results = []
        for hit in data.get("hits", {}).get("hits", []):
            results.append(Record(**hit))

        return results

    def _get_all_template_versions(self) -> List[Template]:
        record_url = f"{self.DEFAULT_BASE}/records/{self.CONCEPT_ID_TEMPLATE}"
        response = requests.get(record_url, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise DataAccessException("Failed to get template versions", details=str(e))
        record_data = response.json()

        # Get all versions
        versions_url = record_data.get("links", {}).get("versions")
        if not versions_url:
            raise DataNotFoundException(
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
                raise DataNotFoundException(
                    f"No template versions found before date {date}"
                )
            correct_template = max(valid_templates, key=lambda t: t.created)
            return correct_template

    def get_record(self, recid: int) -> Record:
        if not recid:
            raise ValueError("id must be an integer")
        url = f"{self.DEFAULT_BASE}/records/{recid}"
        resp = requests.get(url, timeout=30)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise DataAccessException("Failed to get record", details=str(e))
        data = resp.json()
        return Record(**data)

    def download_file_by_id_and_filename(
        self,
        id: int,
        filename: str,
        dest_path: Optional[str] = None,
    ) -> str:
        if not id:
            raise ValueError("id must be an integer")
        record = self.get_record(id)
        if not filename:
            raise ValueError("filename must be a string")
        chosen: File = record.get_child(filename)
        url = chosen.download_url
        if not url:
            raise DataNotFoundException("No download link found for file")

        r = requests.get(url, stream=True, timeout=60)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise DataAccessException("Failed to download file", details=str(e))

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
