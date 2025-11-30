import json
from types import SimpleNamespace

from genson import SchemaBuilder
import jsonschema
from hflav_zenodo.conversors.conversor_interface import ConversorInterface
from hflav_zenodo.exceptions.conversor_exceptions import StructureException
from hflav_zenodo.processing.data_visualizer import DataVisualizer
from hflav_zenodo.logger import get_logger
from dependency_injector.wiring import inject, Provide


logger = get_logger(__name__)


class DynamicConversor(ConversorInterface):
    @inject
    def __init__(self, visualizer: DataVisualizer = Provide["visualizer"]):
        self._visualizer = visualizer

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

    def _validate_json_with_schema(self, schema: dict, json_data: dict):
        try:
            jsonschema.validate(instance=json_data, schema=schema)
        except jsonschema.ValidationError as e:
            raise StructureException(details=str(e))

    def _load_model_from_json(self, data_dict: dict) -> SimpleNamespace:
        model = self._to_namespace(data_dict)
        logger.info("Data loaded successfully. This is the content:")
        self._visualizer.print_json_data(model)
        return model

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

        self._validate_json_with_schema(schema, data_dict)
        return self._load_model_from_json(data_dict)

    def generate_instance_from_local_path(
        self,
        data_path: str,
        schema_path: str = None,
        validate: bool = True,
    ) -> SimpleNamespace:

        if not data_path:
            raise ValueError("Data path must be provided.")

        if validate:
            if schema_path:
                with open(schema_path, "r", encoding="utf-8") as schema_file:
                    schema = json.load(schema_file)
            else:
                schema = self.generate_json_schema(data_path)

            return self.generate_instance_from_schema_and_data(schema, data_path)

        with open(data_path, "r", encoding="utf-8") as data_file:
            data_dict = json.load(data_file)

        return self._load_model_from_json(data_dict)
