import json
from typing import Optional, List, Type

from pydantic import BaseModel
from hflav_zenodo.processing.data_visualizer import DataVisualizer
from hflav_zenodo.conversors.dynamic_conversor import DynamicConversor
from hflav_zenodo.exceptions.source_exceptions import DataAccessException
from hflav_zenodo.models.models import Record
from hflav_zenodo.source.source_interface import SourceInterface


class Services:
    def __init__(self, source: SourceInterface) -> None:
        self._source = source

    def search_records_by_name(
        self, query: Optional[str] = None, size: int = 10, page: int = 1
    ) -> List[Record]:
        try:
            records = self._source.get_records_by_name(
                query=query, size=size, page=page
            )
        except DataAccessException as e:
            print(f"Error while searching records: {e}")
            return []
        print(f"Found {len(records)} records matching query '{query}':")
        for i, record in enumerate(records):
            print(f"{i+1}: {record}")
        return records

    def search_and_load_data_file(
        self, query: Optional[str] = None, size: int = 10, page: int = 1
    ) -> Type[BaseModel]:
        selected_record = 0
        selected_file = 0
        while selected_record == 0:
            records = self.search_records_by_name(query=query, size=size, page=page)
            print("Select a record by number (or 0 to search again):")
            selected_record = int(input())
            if selected_record == 0:
                print("Please enter a new search query:")
                query = input()
            else:
                record = records[selected_record - 1]
                print(f"Selected record: {record.title}")
                print("Select a file by number:")
                selected_file = int(input())
                filename = record.files[selected_file - 1].name
                print(f"Selected file: {filename}")
                return self.load_data_file(record_id=record.id, filename=filename)

    def load_data_file(
        self,
        record_id: int,
        filename: str,
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

        print(
            f"Files downloaded: Template at {template_path}, Data file at {file_path}"
        )
        dynamic_model = DynamicConversor.from_json(template_path)
        ExperimentData = dynamic_model["main"]

        print(f"Loading data from file {file_path} into model...")
        dynamic_class = DynamicConversor.create_instance(ExperimentData, file_path)

        print("Data loaded successfully. This is the content:")
        DataVisualizer.print_summary(dynamic_class, title=record.title)
        DataVisualizer.print_simple(dynamic_class, title=record.title)

        return dynamic_class
