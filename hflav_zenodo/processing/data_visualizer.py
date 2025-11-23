import json
from types import SimpleNamespace
from typing import Any, Type

from pydantic import BaseModel
from rich.table import Table
from rich import print as rprint, print_json


class DataVisualizer:
    """Class to visualize Pydantic models in a simplified and visual way"""

    @staticmethod
    def print_schema(schema: dict):
        print_json(json.dumps(schema))

    @staticmethod
    def print_json_data(data: SimpleNamespace):
        print_json(json.dumps(data.__dict__, indent=4))
