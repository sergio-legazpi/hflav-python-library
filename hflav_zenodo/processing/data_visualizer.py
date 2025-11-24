import json
from types import SimpleNamespace

from rich import print_json

from hflav_zenodo.processing.visualizer_interface import VisualizerInterface


class DataVisualizer(VisualizerInterface):

    def _namespace_to_dict(self, obj):
        if isinstance(obj, SimpleNamespace):
            return {k: self._namespace_to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [self._namespace_to_dict(item) for item in obj]
        else:
            return obj

    def print_schema(self, schema: dict):
        print_json(json.dumps(schema))

    def print_json_data(self, data: SimpleNamespace):
        dict_data = self._namespace_to_dict(data)
        print_json(json.dumps(dict_data, indent=4))
