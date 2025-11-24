import json
from types import SimpleNamespace

from genson import SchemaBuilder
import jsonschema
from hflav_zenodo.conversors.conversor_interface import ConversorInterface
from hflav_zenodo.exceptions.conversor_exceptions import StructureException
from hflav_zenodo.processing.data_visualizer import DataVisualizer
from hflav_zenodo.logger import get_logger

logger = get_logger(__name__)


class DynamicConversor(ConversorInterface):
    def __init__(self):
        self._visualizer = DataVisualizer()

    def _to_namespace(self, obj):
        if isinstance(obj, dict):
            return SimpleNamespace(**{k: self._to_namespace(v) for k, v in obj.items()})
        elif isinstance(obj, list):
            return [self._to_namespace(item) for item in obj]
        else:
            return obj

    def _generate_json_schema(self, file_path: str):
        builder = SchemaBuilder()

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        builder.add_object(data)
        schema = builder.to_schema()

        schema["$schema"] = "http://json-schema.org/draft-07/schema#"

        return schema

    def generate_instance_from_template_and_data(
        self, template_path: str, data_path: str
    ) -> SimpleNamespace:
        if not template_path or not data_path:
            raise ValueError("Template path and data path must be provided.")
        schema = self._generate_json_schema(
            template_path,
        )
        logger.info("Template JSON Schema:")
        self._visualizer.print_schema(schema)

        with open(data_path, "r", encoding="utf-8") as file:
            data_dict = json.load(file)
        try:
            jsonschema.validate(instance=data_dict, schema=schema)
        except jsonschema.ValidationError as e:
            raise StructureException(details=str(e))

        return self._to_namespace(data_dict)
