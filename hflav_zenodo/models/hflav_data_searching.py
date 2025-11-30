from enum import Enum
from types import SimpleNamespace
from typing import List, Union
from dependency_injector.wiring import inject, Provide

from hflav_zenodo.models.base_hflav_data_decorator import BaseHflavDataDecorator
from hflav_zenodo.processing.visualizer_interface import VisualizerInterface
from hflav_zenodo.utils.namespace_utils import dict_to_namespace, namespace_to_dict

from jsonpath_ng.ext import parse


class SearchOperators(Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUALS = ">="
    LESS_THAN_OR_EQUALS = "<="
    CONTAINS = "=~"
    REGEX = "=~"


class HflavDataSearching(BaseHflavDataDecorator):
    @inject
    def __init__(
        self,
        hflav_data: SimpleNamespace,
        visualizer: VisualizerInterface = Provide["visualizer"],
    ):
        super().__init__(hflav_data)
        self._visualizer = visualizer

    def get_data_object_from_key_and_value(
        self,
        object_name: str,
        key_name: str,
        operator: SearchOperators,
        value: Union[str, int, float],
    ) -> List[SimpleNamespace]:
        """
        Retrieve data by name searching recursively through the entire namespace.
        """
        data_dict = namespace_to_dict(self._hflav_data)
        if isinstance(value, str):
            value = f'"{value}"'
        jsonpath_expr = parse(
            f"$..{object_name}[?(@..{key_name} {operator.value} {value})]"
        )
        results = [
            dict_to_namespace(match.value) for match in jsonpath_expr.find(data_dict)
        ]
        for result in results:
            self._visualizer.print_json_data(result)
        return results
