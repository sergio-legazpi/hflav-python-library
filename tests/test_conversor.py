import json
import pytest
from unittest.mock import Mock, patch, mock_open, call
from types import SimpleNamespace
import jsonschema

from hflav_zenodo.conversors.dynamic_conversor import DynamicConversor
from hflav_zenodo.exceptions.conversor_exceptions import StructureException


class TestConversor:
    """Test suite for conversor class focusing on public interface."""

    @pytest.fixture
    def mock_visualizer(self):
        """Mock for DataVisualizer dependency."""
        visualizer = Mock()
        # Configure the mock methods that will be called
        visualizer.print_json_data = Mock()
        visualizer.print_schema = Mock()
        return visualizer

    @pytest.fixture
    def conversor(self, mock_visualizer):
        """Create DynamicConversor instance with mocked dependencies."""
        return DynamicConversor(visualizer=mock_visualizer)

    @pytest.fixture
    def sample_data(self):
        """Sample JSON data for testing."""
        return {"name": "test", "value": 123, "nested": {"field": "nested_value"}}

    @pytest.fixture
    def sample_schema(self):
        """Sample JSON schema for testing."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"},
                "nested": {
                    "type": "object",
                    "properties": {"field": {"type": "string"}},
                },
            },
            "required": ["name", "value"],
        }

    # Test __init__ method - still relevant as part of public contract
    def test_init_with_visualizer(self, mock_visualizer):
        """Test that conversor initializes with visualizer dependency."""
        conversor = DynamicConversor(visualizer=mock_visualizer)
        assert conversor._visualizer == mock_visualizer

    # Test generate_json_schema method - PUBLIC METHOD
    def test_generate_json_schema_success(self, conversor):
        """Test successful schema generation from JSON file."""
        # Test data
        test_data = {"name": "test", "value": 123}
        test_json = json.dumps(test_data)

        # Mock the file operations
        with patch("builtins.open", mock_open(read_data=test_json)) as mock_file:
            # Execute the method
            schema = conversor.generate_json_schema("/test/path.json")

            # Verify file was opened correctly
            mock_file.assert_called_once_with("/test/path.json", "r", encoding="utf-8")

            # Verify the schema has expected structure
            assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
            assert "type" in schema
            assert "properties" in schema

    def test_generate_json_schema_file_not_found(self, conversor):
        """Test schema generation with non-existent file."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                conversor.generate_json_schema("/nonexistent/path.json")

    def test_generate_json_schema_invalid_json(self, conversor):
        """Test schema generation with invalid JSON file."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with pytest.raises(json.JSONDecodeError):
                conversor.generate_json_schema("/invalid/path.json")

    # Test generate_instance_from_schema_and_data method - PUBLIC METHOD
    def test_generate_instance_from_schema_and_data_success(
        self, conversor, mock_visualizer, sample_schema
    ):
        """Test successful instance generation from schema and data."""
        # Test data
        test_data = {"name": "test", "value": 123, "nested": {"field": "value"}}
        test_json = json.dumps(test_data)

        with patch("builtins.open", mock_open(read_data=test_json)):
            # Execute the method
            result = conversor.generate_instance_from_schema_and_data(
                sample_schema, "/test/data.json"
            )

            # Verify visualization was called
            mock_visualizer.print_schema.assert_called_once()

            # Verify the result is a SimpleNamespace
            assert isinstance(result, SimpleNamespace)
            assert result.name == "test"
            assert result.value == 123
            assert result.nested.field == "value"

    def test_generate_instance_from_schema_and_data_validation_error(
        self, conversor, sample_schema
    ):
        """Test instance generation with invalid data."""
        # Test data that doesn't match schema
        invalid_data = {"name": "test", "value": "not_a_number"}
        test_json = json.dumps(invalid_data)

        with patch("builtins.open", mock_open(read_data=test_json)):
            with pytest.raises(StructureException):
                conversor.generate_instance_from_schema_and_data(
                    sample_schema, "/test/data.json"
                )

    def test_generate_instance_from_schema_and_data_missing_arguments(
        self, conversor, sample_schema
    ):
        """Test instance generation with missing arguments."""
        with pytest.raises(ValueError) as exc_info:
            conversor.generate_instance_from_schema_and_data(None, "/path/data.json")
        assert "Schema and data path must be provided" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            conversor.generate_instance_from_schema_and_data(sample_schema, None)
        assert "Schema and data path must be provided" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            conversor.generate_instance_from_schema_and_data(sample_schema, "")
        assert "Schema and data path must be provided" in str(exc_info.value)

    # Test generate_instance_from_local_path method - PUBLIC METHOD
    def test_generate_instance_from_local_path_with_validation_and_schema(
        self, conversor, mock_visualizer, sample_schema
    ):
        """Test loading with schema path and validation enabled."""
        # Test data
        test_data = {"name": "test", "value": 123}
        test_json = json.dumps(test_data)
        schema_json = json.dumps(sample_schema)

        # Mock file operations for both files
        def mock_file_side_effect(path, *args, **kwargs):
            if path == "/test/schema.json":
                return mock_open(read_data=schema_json).return_value
            elif path == "/test/data.json":
                return mock_open(read_data=test_json).return_value
            else:
                return mock_open().return_value

        with patch("builtins.open", side_effect=mock_file_side_effect):
            # Execute the method
            result = conversor.generate_instance_from_local_path(
                data_path="/test/data.json",
                schema_path="/test/schema.json",
                validate=True,
            )

            # Verify the result
            assert isinstance(result, SimpleNamespace)
            assert result.name == "test"
            assert result.value == 123

            # Verify visualization was called
            mock_visualizer.print_schema.assert_called_once()
            mock_visualizer.print_json_data.assert_called_once()

    def test_generate_instance_from_local_path_with_validation_no_schema(
        self, conversor, mock_visualizer
    ):
        """Test loading with validation but no schema path (generates schema from data)."""
        # Test data
        test_data = {"name": "test", "value": 123}
        test_json = json.dumps(test_data)

        with patch("builtins.open", mock_open(read_data=test_json)):
            # Execute the method
            result = conversor.generate_instance_from_local_path(
                data_path="/test/data.json", validate=True
            )

            # Verify the result
            assert isinstance(result, SimpleNamespace)
            assert result.name == "test"
            assert result.value == 123

            # Verify visualization was called (both schema and data)
            # Note: The schema is generated internally, so print_schema might be called
            # with the generated schema
            mock_visualizer.print_json_data.assert_called_once()

    def test_generate_instance_from_local_path_without_validation(
        self, conversor, mock_visualizer
    ):
        """Test loading without validation."""
        # Test data
        test_data = {"name": "test", "value": 123}
        test_json = json.dumps(test_data)

        with patch("builtins.open", mock_open(read_data=test_json)):
            # Execute the method
            result = conversor.generate_instance_from_local_path(
                data_path="/test/data.json", validate=False
            )

            # Verify the result
            assert isinstance(result, SimpleNamespace)
            assert result.name == "test"
            assert result.value == 123

            # Verify only data visualization was called (no schema validation)
            mock_visualizer.print_json_data.assert_called_once()
            # Schema visualization should NOT be called when validate=False
            mock_visualizer.print_schema.assert_not_called()

    def test_generate_instance_from_local_path_missing_data_path(self, conversor):
        """Test loading with missing data path."""
        with pytest.raises(ValueError) as exc_info:
            conversor.generate_instance_from_local_path(data_path=None)
        assert "Data path must be provided" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            conversor.generate_instance_from_local_path(data_path="")
        assert "Data path must be provided" in str(exc_info.value)

    def test_generate_instance_from_local_path_file_not_found(self, conversor):
        """Test loading with non-existent file."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                conversor.generate_instance_from_local_path(
                    data_path="/nonexistent/path.json", validate=False
                )

    def test_generate_instance_from_local_path_invalid_json(self, conversor):
        """Test loading with invalid JSON file."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with pytest.raises(json.JSONDecodeError):
                conversor.generate_instance_from_local_path(
                    data_path="/invalid.json", validate=False
                )

    # Test edge cases for public methods
    def test_generate_instance_from_schema_and_data_empty_data(
        self, conversor, sample_schema
    ):
        """Test instance generation with empty data."""
        empty_data = {}
        test_json = json.dumps(empty_data)

        with patch("builtins.open", mock_open(read_data=test_json)):
            with pytest.raises(StructureException):
                # This should fail validation since schema requires name and value
                conversor.generate_instance_from_schema_and_data(
                    sample_schema, "/test/data.json"
                )

    def test_generate_instance_from_local_path_empty_file(self, conversor):
        """Test loading with empty file."""
        with patch("builtins.open", mock_open(read_data="")):
            with pytest.raises(json.JSONDecodeError):
                conversor.generate_instance_from_local_path(
                    data_path="/empty.json", validate=False
                )

    def test_generate_instance_from_local_path_schema_not_found(self, conversor):
        """Test loading when schema file is not found but validation is requested."""
        # Test data
        test_data = {"name": "test", "value": 123}
        test_json = json.dumps(test_data)

        def mock_file_side_effect(path, *args, **kwargs):
            if path == "/test/schema.json":
                raise FileNotFoundError("Schema not found")
            elif path == "/test/data.json":
                return mock_open(read_data=test_json).return_value

        with patch("builtins.open", side_effect=mock_file_side_effect):
            with pytest.raises(FileNotFoundError):
                conversor.generate_instance_from_local_path(
                    data_path="/test/data.json",
                    schema_path="/test/schema.json",
                    validate=True,
                )

    # Integration-style test
    def test_full_workflow(self, conversor, mock_visualizer):
        """Test a complete workflow: generate schema, then use it to validate data."""
        # Test data
        test_data = {"name": "workflow_test", "value": 999}
        test_json = json.dumps(test_data)

        # Step 1: Generate schema from data
        with patch("builtins.open", mock_open(read_data=test_json)):
            schema = conversor.generate_json_schema("/test/data.json")

            # Verify schema was generated
            assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

            # Step 2: Use the generated schema to validate the same data
            # (re-open the file for the second call)
            with patch("builtins.open", mock_open(read_data=test_json)):
                result = conversor.generate_instance_from_schema_and_data(
                    schema, "/test/data.json"
                )

                # Verify the result
                assert isinstance(result, SimpleNamespace)
                assert result.name == "workflow_test"
                assert result.value == 999

                # Verify visualizations were called
                assert mock_visualizer.print_schema.call_count >= 1
                assert mock_visualizer.print_json_data.call_count >= 1
