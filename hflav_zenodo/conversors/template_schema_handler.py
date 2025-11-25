from hflav_zenodo import logger
from hflav_zenodo.conversors.conversor_handler import ConversorHandler
from hflav_zenodo.models.models import Template

logger = logger.get_logger(__name__)


class TemplateSchemaHandler(ConversorHandler):
    """Handler for Template schema conversor.

    It's the last handler in the chain of responsibility for processing

    It is triggered when the previous handlers fail to get the schema.

    In this scenario, the handler creates a schema based on the template of the Zenodo record.
    """

    def handle(self, template: Template, data_path: str) -> object:
        logger.info("TemplateSchemaHandler: Handling the request...")
        if not self.can_handle(template, data_path):
            raise Exception("No handler available for this template and data path")
        logger.info(f"Downloading template file {template.jsontemplate.name}...")
        template_path = self._source.download_file_by_id_and_filename(
            id=template.rec_id, filename=template.jsontemplate.name
        )

        logger.info(f"Template downloaded: Template at {template_path}")
        logger.info(f"Loading data from file {data_path} into model...")
        schema = self._conversor.generate_json_schema(
            template_path,
        )
        dynamic_class = self._conversor.generate_instance_from_schema_and_data(
            schema, data_path
        )
        return dynamic_class

    def can_handle(self, template: Template, data_path: str) -> bool:
        return template.jsontemplate

    def set_next(self, handler: "ConversorHandler") -> "ConversorHandler":
        self._next_handler = handler
        return handler
