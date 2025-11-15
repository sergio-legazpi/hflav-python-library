from typing import Optional, List
from hflav_zenodo.models.models import Record
from hflav_zenodo.source.source_interface import SourceInterface


class Services:
    def __init__(self, source: SourceInterface) -> None:
        self._source = source

    def search_records_by_name(
        self, query: Optional[str] = None, size: int = 10, page: int = 1
    ) -> List[Record]:
        records = self._source.get_records_by_name(query=query, size=size, page=page)
        return records

    def load_data_file(
        self,
        record_id: int,
        filename: Optional[str] = None,
        dest_path: Optional[str] = None,
    ) -> str:
        record = self._source.get_record(recid=record_id)
        template = self._source.get_correct_template_by_date(date=record.created)
        template_path = self._source.download_file_by_id_and_filename(
            id=template.rec_id, filename=template.jsons[0].name
        )
        file_path = self._source.download_file_by_id_and_filename(
            id=record_id, filename=filename, dest_path=dest_path
        )
        return template_path + " // " + file_path
