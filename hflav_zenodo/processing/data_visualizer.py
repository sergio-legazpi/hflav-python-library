from typing import Any

from pydantic import BaseModel
from rich.table import Table
from rich import print as rprint


class DataVisualizer:
    """Class to visualize Pydantic models in a simplified and visual way"""

    @staticmethod
    def print_simple(obj: BaseModel, title: str = "Datos del Experimento"):
        """Print object in a simplified format"""
        print(f"\n{'='*50}")
        print(f"📊 {title}")
        print(f"{'='*50}")
        DataVisualizer._print_recursive(obj, "")
        print(f"{'='*50}\n")

    @staticmethod
    def _print_recursive(obj: Any, indent: str, is_last: bool = True):
        """Recursively print object structure"""
        if isinstance(obj, BaseModel):
            # Print model fields
            fields = obj.__dict__
            connector = "└── " if is_last else "├── "

            for i, (key, value) in enumerate(fields.items()):
                is_last_field = i == len(fields) - 1
                new_connector = "    " if is_last else "│   "

                if value is None:
                    print(f"{indent}{connector}{key}: [None]")
                elif isinstance(value, (str, int, float, bool)):
                    # Truncate long values for better visualization
                    display_value = str(value)
                    if len(display_value) > 50:
                        display_value = display_value[:47] + "..."
                    print(f"{indent}{connector}{key}: {display_value}")
                elif isinstance(value, BaseModel):
                    print(f"{indent}{connector}{key}:")
                    DataVisualizer._print_recursive(
                        value, indent + new_connector, is_last_field
                    )
                elif isinstance(value, list):
                    print(f"{indent}{connector}{key} [{len(value)} items]:")
                    if value and isinstance(value[0], BaseModel):
                        for j, item in enumerate(value):
                            item_is_last = j == len(value) - 1
                            DataVisualizer._print_recursive(
                                item, indent + new_connector + "    ", item_is_last
                            )
                    else:
                        for j, item in enumerate(value):
                            item_is_last = j == len(value) - 1
                            item_connector = "└── " if item_is_last else "├── "
                            display_item = str(item)
                            if len(display_item) > 30:
                                display_item = display_item[:27] + "..."
                            print(
                                f"{indent}{new_connector}    {item_connector}{display_item}"
                            )

    @staticmethod
    def print_summary(obj: BaseModel, title: str = "Resumen del Experimento"):
        """Print a summary table of the object"""
        table = Table(
            title=f"📈 {title}", show_header=True, header_style="bold magenta"
        )
        table.add_column("Field", style="cyan", width=50)
        table.add_column("Type", style="green", width=15)
        table.add_column("Value/Items", style="yellow", width=25)

        DataVisualizer._add_to_table(obj, table)
        rprint(table)

    @staticmethod
    def _add_to_table(obj: Any, table: Table, prefix: str = ""):
        """Add object data to rich table"""
        if isinstance(obj, BaseModel):
            for key, value in obj.__dict__.items():
                full_key = f"{prefix}{key}" if prefix else key

                if value is None:
                    table.add_row(full_key, "None", "∅")
                elif isinstance(value, (str, int, float, bool)):
                    display_value = str(value)
                    if len(display_value) > 20:
                        display_value = display_value[:17] + "..."
                    table.add_row(full_key, type(value).__name__, display_value)
                elif isinstance(value, BaseModel):
                    table.add_row(full_key, "Object", "→ View details")
                    DataVisualizer._add_to_table(value, table, f"{full_key}.")
                elif isinstance(value, list):
                    item_type = "Mixed"
                    if value:
                        first_type = type(value[0]).__name__
                        if all(isinstance(x, type(value[0])) for x in value):
                            item_type = f"List[{first_type}]"

                    table.add_row(full_key, item_type, f"{len(value)} items")
                    if value and isinstance(value[0], BaseModel):
                        DataVisualizer._add_to_table(value[0], table, f"{full_key}[0].")
