from types import SimpleNamespace
from typing import Optional, List

from pydantic import BaseModel
from hflav_zenodo.conversors.conversor_interface import ConversorInterface
from hflav_zenodo.conversors.gitlab_schema_handler import GitlabSchemaHandler
from hflav_zenodo.conversors.template_schema_handler import TemplateSchemaHandler
from hflav_zenodo.conversors.zenodo_schema_handler import ZenodoSchemaHandler
from hflav_zenodo.processing.data_visualizer import DataVisualizer
from hflav_zenodo.conversors.dynamic_conversor import DynamicConversor
from hflav_zenodo.exceptions.source_exceptions import DataAccessException
from hflav_zenodo.models.models import Record
from hflav_zenodo.processing.visualizer_interface import VisualizerInterface
from hflav_zenodo.source.source_interface import SourceInterface
from hflav_zenodo.logger import get_logger

logger = get_logger(__name__)


class Services:
    def __init__(
        self,
        source: SourceInterface,
        conversor: ConversorInterface,
        visualizer: VisualizerInterface,
    ) -> None:
        self._source = source
        self._conversor = conversor
        self._visualizer = visualizer

    def search_records_by_name(
        self, query: Optional[str] = None, size: int = 10, page: int = 1
    ) -> List[Record]:
        try:
            records = self._source.get_records_by_name(
                query=query, size=size, page=page
            )
        except DataAccessException as e:
            logger.error(f"Error while searching records: {e}")
            return []
        logger.info(f"Found {len(records)} records matching query '{query}':")
        for i, record in enumerate(records):
            logger.info(f"{i+1}: {record}")
        return records

    def search_and_load_data_file(
        self, query: Optional[str] = None, size: int = 10, page: int = 1
    ) -> SimpleNamespace:
        selected_record = 0
        selected_file = 0
        while selected_record == 0:
            records = self.search_records_by_name(query=query, size=size, page=page)
            logger.info("Select a record by number (or 0 to search again):")
            selected_record = int(input())
            if selected_record == 0:
                logger.info("Please enter a new search query:")
                query = input()
            else:
                record = records[selected_record - 1]
                logger.info(f"Selected record: {record.title}")
                logger.info("Select a file by number:")
                selected_file = int(input())
                filename = record.children[selected_file - 1].name
                logger.info(f"Selected file: {filename}")
                return self.load_data_file(record_id=record.id, filename=filename)

    def load_data_file(
        self,
        record_id: int,
        filename: str,
        dest_path: Optional[str] = None,
    ) -> SimpleNamespace:

        logger.info(f"Getting record with id {record_id}...")
        record = self._source.get_record(recid=record_id)

        logger.info(f"Record found: {record.title}")
        logger.info(
            f"Getting correct template for the record with creation date {record.created}..."
        )
        template = self._source.get_correct_template_by_date(date=record.created)

        logger.info(
            f"Template found: {template.title}, with version {template.version}"
        )

        logger.info(f"Downloading record file {filename}...")
        file_path = self._source.download_file_by_id_and_filename(
            id=record_id, filename=filename, dest_path=dest_path
        )
        logger.info(f"Downloaded record file {filename} to {file_path}")

        logger.info("Setting up the chain of responsibility for schema handling...")
        zenodo_schema_handler = ZenodoSchemaHandler(
            source=self._source, conversor=self._conversor, visualizer=self._visualizer
        )
        gitlab_schema_handler = GitlabSchemaHandler(
            source=self._source, conversor=self._conversor, visualizer=self._visualizer
        )
        template_schema_handler = TemplateSchemaHandler(
            source=self._source, conversor=self._conversor, visualizer=self._visualizer
        )

        zenodo_schema_handler.set_next(gitlab_schema_handler).set_next(
            template_schema_handler
        )
        logger.info("Chain of responsibility for schema handling set up successfully.")

        return zenodo_schema_handler.handle(template, file_path)
