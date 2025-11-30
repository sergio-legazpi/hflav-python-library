from abc import ABC, abstractmethod
from types import SimpleNamespace


class ConversorInterface(ABC):
    """Abstract interface for conversion from template and data to domain objects used by HFLAV.

    This defines the public contract to convert HFLAV data. Implementations must provide the methods below and
    follow the documented input/output shapes.
    """

    @abstractmethod
    def generate_json_schema(self, file_path: str) -> dict:
        """Generate a JSON schema from a data file."""
        pass

    @abstractmethod
    def generate_instance_from_schema_and_data(
        self, schema: dict, data_path: str
    ) -> SimpleNamespace:
        """Generate an instance from a schema and data files.

        Args:
                schema: JSON schema as a dictionary
                data_path: path to the JSON data file

        Returns:
                An instance validated and generated from the schema and data files
        Raises:
                ValueError: If the schema or data files are invalid.
                StructureException: If the data structure does not match the schema format.

        """
        pass

    @abstractmethod
    def generate_instance_from_local_path(
        self,
        data_path: str,
        schema_path: str = None,
        validate: bool = True,
    ) -> SimpleNamespace:
        """
        Load a local data file from a given path, optionally validating against a schema.

        Returns:
            An instance generated from the data files

        Raises:
            ValueError: If the data file is invalid.
            StructureException: If validation is enabled and the data structure does not match the schema format.
        """
        pass
