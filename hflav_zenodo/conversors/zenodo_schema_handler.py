import json
from hflav_zenodo import logger
from types import SimpleNamespace
from hflav_zenodo.conversors.conversor_handler import ConversorHandler
from hflav_zenodo.models.models import Template

logger = logger.get_logger(__name__)


class ZenodoSchemaHandler(ConversorHandler):
    """Handler for Zenodo schema conversor.

    It's the first handler in the chain of responsibility for processing

    It is triggered when the schema is found inside Zenodo records.

    If it cannot handle the request, it passes it to the next handler in the chain.
    """

    def handle(self, template: Template, data_path: str) -> SimpleNamespace:
        logger.info("ZenodoSchemaHandler: Handling the request...")
        if not self.can_handle(template, data_path):
            logger.info(
                "ZenodoSchemaHandler: Cannot handle the request, passing to next handler..."
            )
            return self._next_handler.handle(template, data_path)
        logger.info(f"Downloading JSON schema file {template.jsonschema.name}...")
        schema_path = self._source.download_file_by_id_and_filename(
            id=template.rec_id, filename=template.jsonschema.name
        )
        logger.info(f"JSON schema downloaded: Schema at {schema_path}")
        with open(schema_path, "r", encoding="utf-8") as file:
            schema = json.load(file)

        dynamic_class = self._conversor.generate_instance_from_schema_and_data(
            schema, data_path
        )
        return dynamic_class

    def can_handle(self, template: Template, data_path: str) -> bool:
        return template.jsonschema

    def set_next(self, handler: "ConversorHandler") -> "ConversorHandler":
        self._next_handler = handler
        return handler
