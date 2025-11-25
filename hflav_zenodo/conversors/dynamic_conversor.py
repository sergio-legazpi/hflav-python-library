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

    def _avoid_extra_fields(self, obj):
        if isinstance(obj, dict):
            if obj.get("type") == "object":
                obj["additionalProperties"] = False
            for v in obj.values():
                self._avoid_extra_fields(v)
        elif isinstance(obj, list):
            for item in obj:
                self._avoid_extra_fields(item)

    def generate_json_schema(self, file_path: str) -> dict:
        builder = SchemaBuilder()

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        builder.add_object(data)
        schema = builder.to_schema()

        schema["$schema"] = "http://json-schema.org/draft-07/schema#"

        self._avoid_extra_fields(schema)

        return schema

    def generate_instance_from_schema_and_data(
        self, schema: dict, data_path: str
    ) -> SimpleNamespace:
        if not schema or not data_path:
            raise ValueError("Schema and data path must be provided.")
        logger.info("JSON Schema:")
        self._visualizer.print_schema(schema)

        with open(data_path, "r", encoding="utf-8") as file:
            data_dict = json.load(file)
        try:
            jsonschema.validate(instance=data_dict, schema=schema)
        except jsonschema.ValidationError as e:
            raise StructureException(details=str(e))
        model = self._to_namespace(data_dict)
        logger.info("Data loaded successfully. This is the content:")
        self._visualizer.print_json_data(model)
        return model
