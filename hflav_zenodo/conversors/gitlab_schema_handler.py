from dependency_injector.wiring import inject, Provide

from hflav_zenodo import logger

from hflav_zenodo.conversors.conversor_handler import ConversorHandler
from hflav_zenodo.conversors.conversor_interface import ConversorInterface
from hflav_zenodo.exceptions.source_exceptions import (
    NoSchemaFoundInsideGitlabRepository,
    NoVersionTagFound,
)
from hflav_zenodo.models.models import Template
from hflav_zenodo.processing.visualizer_interface import VisualizerInterface
from hflav_zenodo.source.source_gitlab_interface import SourceGitlabInterface
from hflav_zenodo.source.source_interface import SourceInterface

logger = logger.get_logger(__name__)


class GitlabSchemaHandler(ConversorHandler):
    """Handler for Gitlab schema conversor.

    It's triggered when the first handler fails and the schema can be found inside Gitlab repository.

    If it cannot handle the request, it passes it to the next handler in the chain.
    """

    @inject
    def __init__(
        self,
        source: SourceInterface = Provide["source"],
        conversor: ConversorInterface = Provide["conversor"],
        visualizer: VisualizerInterface = Provide["visualizer"],
        gitlab_source: SourceGitlabInterface = Provide["gitlab_source"],
    ):
        super().__init__(source=source, conversor=conversor, visualizer=visualizer)
        self._source_gitlab_client = gitlab_source

    def _try_to_get_schema_version(self, data_path: str) -> str:
        with open(data_path, "r", encoding="utf-8") as file:
            data_lines = file.readlines()
            for line in data_lines:
                if "schema" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        version = parts[1].strip().strip('",')
                        return version
        return "main"

    def handle(self, template: Template, data_path: str) -> object:
        logger.info("Handling the request...")
        if not self.can_handle(template, data_path):
            logger.info("Cannot handle the request, passing to next handler...")
            return self._next_handler.handle(template, data_path)
        try:
            schema_dict = self._source_gitlab_client.get_schema_inside_repository(
                self._try_to_get_schema_version(data_path)
            )
        except (
            ValueError,
            NoSchemaFoundInsideGitlabRepository,
            NoVersionTagFound,
        ) as e:
            logger.error(f"Error retrieving schema from GitLab: {e.message}")
            logger.info("Passing to next handler...")
            return self._next_handler.handle(template, data_path)
        logger.info("Schema retrieved successfully.")
        logger.info(f"Loading data from file {data_path} into model...")
        dynamic_class = self._conversor.generate_instance_from_schema_and_data(
            schema_dict, data_path
        )

        return dynamic_class

    def can_handle(self, template: Template, data_path: str) -> bool:
        return template.jsontemplate

    def set_next(self, handler: "ConversorHandler") -> "ConversorHandler":
        self._next_handler = handler
        return handler
