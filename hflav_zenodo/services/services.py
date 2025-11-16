from typing import Optional, List, Type

from pydantic import BaseModel
from hflav_zenodo.conversors.dynamic_conversor import DynamicConversor
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
    ) -> Type[BaseModel]:
        print(f"Getting record with id {record_id}...")
        record = self._source.get_record(recid=record_id)

        print(f"Record found: {record.title}")
        print(
            f"Getting correct template for the record with creation date {record.created}..."
        )
        template = self._source.get_correct_template_by_date(date=record.created)

        print(f"Template found: {template.title}, with version {template.version}")
        print(f"Downloading template file {template.jsons[0].name}...")
        template_path = self._source.download_file_by_id_and_filename(
            id=template.rec_id, filename=template.jsons[0].name
        )

        print(f"Downloading record file {filename}...")
        file_path = self._source.download_file_by_id_and_filename(
            id=record_id, filename=filename, dest_path=dest_path
        )

        print(f"Files downloaded: Template at {template_path}, Record at {file_path}")
        dynamic_model = DynamicConversor.from_json(template_path)
        ExperimentData = dynamic_model["main"]

        print(f"Loading data from file {file_path} into model...")
        return DynamicConversor.create_instance(ExperimentData, file_path)
