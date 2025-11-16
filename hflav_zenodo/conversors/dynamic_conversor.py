import json
import os
from typing import Any, Dict, Type, Union, List, Optional

from pydantic import BaseModel, create_model


class DynamicConversor(BaseModel):
    """Base class to create Pydantic models dynamically from JSON templates"""

    @classmethod
    def from_json(
        cls, json_template: Union[str, bytes, os.PathLike, Dict]
    ) -> Dict[str, Type[BaseModel]]:
        """
        Create Pydantic models from a JSON template with ALL fields optional

        Args:
            json_template: JSON string, file path, or dict with example data

        Returns:
            Dictionary with model names and their classes
        """
        if isinstance(json_template, dict):
            # Already a dictionary
            example_data = json_template
        elif isinstance(json_template, (str, bytes, os.PathLike)) and os.path.exists(
            json_template
        ):
            # Is a file path
            with open(json_template, "r", encoding="utf-8") as file:
                example_data = json.load(file)
        else:
            # Is a JSON string
            example_data = json.loads(json_template)

        models = {}

        def _create_model(name: str, data: Any) -> Type[BaseModel]:
            """
            Recursive function to create models with all fields optional
            """
            if not isinstance(data, dict):
                # For non-dict data, create a simple model with optional value
                field_type = cls._infer_type(data)
                return create_model(name, value=(Optional[field_type], None))

            fields = {}

            for key, value in data.items():
                field_name = key

                if isinstance(value, dict):
                    # Create sub-model recursively
                    submodel_name = f"{name}_{key}"
                    nested_model = _create_model(submodel_name, value)
                    fields[field_name] = (Optional[nested_model], None)
                elif isinstance(value, list) and value:
                    # Handle lists
                    first_item = value[0]
                    if isinstance(first_item, dict):
                        # List of objects
                        submodel_name = f"{name}_{key}_item"
                        model_item = _create_model(submodel_name, first_item)
                        fields[field_name] = (Optional[List[model_item]], None)  # type: ignore
                    else:
                        # List of primitive types
                        item_type = cls._infer_type(first_item)
                        fields[field_name] = (Optional[List[item_type]], None)  # type: ignore
                else:
                    # Primitive type - all fields are optional
                    field_type = cls._infer_type(value)
                    fields[field_name] = (Optional[field_type], None)

            return create_model(name, **fields)

        # Create main model
        main_model_name = "ExperimentData"
        models["main"] = _create_model(main_model_name, example_data)

        return models

    @classmethod
    def _infer_type(cls, value: Any) -> Type:
        """Infer the appropriate type for a value"""
        if value is None:
            return Any
        elif isinstance(value, bool):
            return bool
        elif isinstance(value, int):
            return int
        elif isinstance(value, float):
            return float
        elif isinstance(value, str):
            return str
        elif isinstance(value, list):
            if value:
                item_type = cls._infer_type(value[0])
                return List[item_type]  # type: ignore
            return List[Any]  # type: ignore
        elif isinstance(value, dict):
            # For nested dicts, we'll handle recursively in _create_model
            return Any
        else:
            return Any

    @classmethod
    def create_instance(cls, model: Type[BaseModel], file_path: str) -> BaseModel:
        """
        Create an instance of the model with real data
        Args:
            model: Pydantic model class
            data: Dictionary with real data

        Returns:
            Validated model instance
        """
        with open(file_path, "r", encoding="utf-8") as file:
            loaded_data = json.load(file)
        return model(**loaded_data)
