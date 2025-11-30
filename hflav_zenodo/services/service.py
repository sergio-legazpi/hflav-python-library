from types import SimpleNamespace
from typing import Optional, List

from dependency_injector.wiring import inject, Provide

from hflav_zenodo.conversors.conversor_interface import ConversorInterface
from hflav_zenodo.exceptions.source_exceptions import DataAccessException
from hflav_zenodo.filters.base_query import BaseQuery
from hflav_zenodo.models.models import Record
from hflav_zenodo.services.command import CommandInvoker
from hflav_zenodo.services.search_and_load_data_file_command import (
    SearchAndLoadDataFile,
)
from hflav_zenodo.source.source_interface import SourceInterface
from hflav_zenodo.logger import get_logger
from hflav_zenodo.services.service_interface import ServiceInterface

logger = get_logger(__name__)


class Service(ServiceInterface):
    @inject
    def __init__(
        self,
        source: SourceInterface = Provide["source"],
        conversor: ConversorInterface = Provide["conversor"],
        command_invoker: CommandInvoker = Provide["command_invoker"],
        handler_schema_chain=Provide["handler_schema_chain"],
    ) -> None:
        self._source = source
        self._conversor = conversor
        self._command_invoker = command_invoker
        self._handler_schema_chain = handler_schema_chain

    def search_records_by_name(self, query: BaseQuery) -> List[Record]:
        try:
            records = self._source.get_records_by_name(query=query)
        except DataAccessException as e:
            logger.error(f"Error while searching records: {e}")
            return []
        logger.info(f"Found {len(records)} records matching query '{str(query)}':")
        for i, record in enumerate(records):
            logger.info(f"{i+1}: {record}")
        return records

    def search_and_load_data_file(self, query: BaseQuery) -> SimpleNamespace:
        self._command_invoker.set_command(
            SearchAndLoadDataFile(service=self, query=query)
        )
        return self._command_invoker.execute_command()

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

        return self._handler_schema_chain.handle(template, file_path)

    def load_local_data_file_from_path(
        self,
        file_path: str,
        schema_path: Optional[str] = None,
        validate: bool = True,
    ) -> SimpleNamespace:
        return self._conversor.generate_instance_from_local_path(
            data_path=file_path,
            schema_path=schema_path,
            validate=validate,
        )

    def plot_data(
        self, data_object: SimpleNamespace, save_path: Optional[str] = None
    ) -> None:
        return NotImplementedError("Method not implemented yet.")
