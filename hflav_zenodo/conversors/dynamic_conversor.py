import json
import os
from typing import Any, Dict, Type, Union, List, Optional

from pydantic import BaseModel, create_model


class DynamicConversor(BaseModel):
    """Base class to create Pydantic models dynamically from JSON templates"""

    def _get_data_from_dict_file_or_string(
        self, input_data: Union[str, bytes, os.PathLike, Dict]
    ) -> Dict:
        """
        Load data from a dictionary, JSON string, or file path

        Args:
            input_data: JSON string, file path, or dict with example data
        Returns:
            Dictionary with loaded data
        """
        if isinstance(input_data, dict):
            # Already a dictionary
            return input_data
        elif isinstance(input_data, (str, bytes, os.PathLike)) and os.path.exists(
            input_data
        ):
            # Is a file path
            with open(input_data, "r", encoding="utf-8") as file:
                return json.load(file)
        else:
            # Is a JSON string
            return json.loads(input_data)

    @classmethod
    def from_json(
        cls, json_template: Union[str, bytes, os.PathLike, Dict]
    ) -> Dict[str, Type[BaseModel]]:
        """
        Create Pydantic models from a JSON template with ALL fields as Union and Optional

        Args:
            json_template: JSON string, file path, or dict with example data

        Returns:
            Dictionary with model names and their classes
        """
        example_data = cls._get_data_from_dict_file_or_string(cls, json_template)

        models = {}

        def _create_model(name: str, data: Any) -> Type[BaseModel]:
            """
            Recursive function to create models with all fields as Union and Optional
            """
            if not isinstance(data, dict):
                # For non-dict data, create a simple model with Union and Optional
                field_types = cls._infer_types(data)
                union_type = (
                    Union[tuple(field_types)]
                    if len(field_types) > 1
                    else field_types[0]
                )
                return create_model(name, value=(Optional[union_type], None))

            fields = {}

            for key, value in data.items():
                field_name = key

                if isinstance(value, dict):
                    # Create sub-model recursively
                    submodel_name = f"{name}_{key}"
                    nested_model = _create_model(submodel_name, value)
                    field_types = [nested_model, type(None)]
                    fields[field_name] = (Optional[Union[tuple(field_types)]], None)
                elif isinstance(value, list) and value:
                    # Handle lists - collect all types from all items
                    item_types = set()
                    for item in value:
                        if isinstance(item, dict):
                            # List of objects
                            submodel_name = f"{name}_{key}_item"
                            model_item = _create_model(submodel_name, item)
                            item_types.add(model_item)
                        else:
                            # Collect all primitive types found in the list
                            primitive_types = cls._infer_types(item)
                            item_types.update(primitive_types)

                    if item_types:
                        # Create Union type for list items
                        list_item_type = (
                            Union[tuple(item_types)]
                            if len(item_types) > 1
                            else next(iter(item_types))
                        )
                        list_type = List[list_item_type]  # type: ignore
                        fields[field_name] = (Optional[list_type], None)
                    else:
                        # Empty list or no types found
                        fields[field_name] = (Optional[List[Any]], None)
                else:
                    # Primitive type - all fields are Union and Optional
                    field_types = cls._infer_types(value)
                    union_type = (
                        Union[tuple(field_types)]
                        if len(field_types) > 1
                        else field_types[0]
                    )
                    fields[field_name] = (Optional[union_type], None)

            return create_model(name, **fields)

        # Create main model
        main_model_name = "ExperimentData"
        models["main"] = _create_model(main_model_name, example_data)

        return models

    @classmethod
    def _infer_types(cls, value: Any) -> List[Type]:
        """Infer all possible types for a value, collecting multiple types"""
        types_found = set()

        def _collect_types(val: Any):
            if val is None:
                types_found.add(type(None))
            elif isinstance(val, bool):
                types_found.add(bool)
            elif isinstance(val, int):
                types_found.add(int)
            elif isinstance(val, float):
                types_found.add(float)
            elif isinstance(val, str):
                types_found.add(str)
            elif isinstance(val, list):
                types_found.add(list)
                # Recursively collect types from list items
                for item in val:
                    _collect_types(item)
            elif isinstance(val, dict):
                types_found.add(dict)
                # Recursively collect types from dict values
                for dict_val in val.values():
                    _collect_types(dict_val)
            else:
                types_found.add(type(val))

        _collect_types(value)

        # Convert to list and ensure type(None) is included for Optional compatibility
        result_types = list(types_found)

        # If we only found basic types and no None, ensure Optional can work
        if type(None) not in result_types:
            # We'll let the caller handle adding None for Optional
            pass

        return result_types if result_types else [Any]

    @classmethod
    def create_instance(
        cls, model: Type[BaseModel], data: Union[Dict, str, bytes, os.PathLike]
    ) -> BaseModel:
        """
        Create an instance of the model with real data
        Args:
            model: Pydantic model class
            data: Dictionary with real data

        Returns:
            Validated model instance
        """
        loaded_data = cls._get_data_from_dict_file_or_string(cls, data)
        return model(**loaded_data)
