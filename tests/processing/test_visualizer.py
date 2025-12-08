import pytest
import json
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, call

from hflav_zenodo.processing.visualizer_interface import VisualizerInterface
from hflav_zenodo.processing.data_visualizer import DataVisualizer


class TestVisualizer:
    """Test suite for DataVisualizer focusing on the public interface."""

    def test_implements_visualizer_interface(self):
        """Test that DataVisualizer correctly implements VisualizerInterface."""
        visualizer = DataVisualizer()
        assert isinstance(visualizer, VisualizerInterface)

    def test_print_schema_method_signature(self):
        """Test that print_schema accepts a dict parameter."""
        visualizer = DataVisualizer()

        # Test with valid schema dictionary
        test_schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        # Patch both json.dumps and print_json
        with patch(
            "hflav_zenodo.processing.data_visualizer.json.dumps"
        ) as mock_dumps, patch(
            "hflav_zenodo.processing.data_visualizer.print_json"
        ) as mock_print_json:

            # Setup the mock return
            mock_dumps.return_value = (
                '{"type": "object", "properties": {"name": {"type": "string"}}}'
            )

            visualizer.print_schema(test_schema)

            # Verify json.dumps was called with the schema
            mock_dumps.assert_called_once_with(test_schema)

            # Verify print_json was called with the JSON string
            mock_print_json.assert_called_once_with(mock_dumps.return_value)

    def test_print_json_data_method_signature(self):
        """Test that print_json_data accepts a SimpleNamespace parameter."""
        visualizer = DataVisualizer()

        # Create test data with SimpleNamespace
        test_data = SimpleNamespace(name="test", value=123)

        with patch(
            "hflav_zenodo.processing.data_visualizer.namespace_to_dict"
        ) as mock_namespace_to_dict, patch(
            "hflav_zenodo.processing.data_visualizer.json.dumps"
        ) as mock_dumps, patch(
            "hflav_zenodo.processing.data_visualizer.print_json"
        ) as mock_print_json:

            # Mock the conversions
            mock_dict = {"name": "test", "value": 123}
            mock_namespace_to_dict.return_value = mock_dict
            mock_dumps.return_value = '{"name": "test", "value": 123}'

            visualizer.print_json_data(test_data)

            # Verify namespace_to_dict was called with the SimpleNamespace
            mock_namespace_to_dict.assert_called_once_with(test_data)

            # Verify json.dumps was called with proper arguments
            mock_dumps.assert_called_once_with(mock_dict, indent=4)

            # Verify print_json was called
            mock_print_json.assert_called_once_with(mock_dumps.return_value)

    def test_print_schema_with_various_schema_types(self):
        """Test print_schema handles different schema structures correctly."""
        visualizer = DataVisualizer()

        test_cases = [
            {},
            {"type": "string"},
        ]

        for schema in test_cases:
            # Use a simple string for the mock return
            mock_json_string = "mock_json_string"

            with patch(
                "hflav_zenodo.processing.data_visualizer.json.dumps"
            ) as mock_dumps, patch(
                "hflav_zenodo.processing.data_visualizer.print_json"
            ) as mock_print_json:

                mock_dumps.return_value = mock_json_string

                visualizer.print_schema(schema)

                # Verify json.dumps was called with the schema
                mock_dumps.assert_called_once_with(schema)

                # Verify print_json was called with the JSON string
                mock_print_json.assert_called_once_with(mock_json_string)

    def test_print_json_data_with_various_data_structures(self):
        """Test print_json_data handles different data structures correctly."""
        visualizer = DataVisualizer()

        test_cases = [
            # Simple namespace
            SimpleNamespace(name="John", age=30),
            # Nested namespace
            SimpleNamespace(
                user=SimpleNamespace(
                    name="Alice",
                    settings=SimpleNamespace(theme="dark", notifications=True),
                )
            ),
            # Namespace with list
            SimpleNamespace(items=[1, 2, 3], metadata=SimpleNamespace(count=3)),
            # Empty namespace
            SimpleNamespace(),
        ]

        for test_data in test_cases:
            with patch(
                "hflav_zenodo.processing.data_visualizer.namespace_to_dict"
            ) as mock_namespace_to_dict, patch(
                "hflav_zenodo.processing.data_visualizer.json.dumps"
            ) as mock_dumps, patch(
                "hflav_zenodo.processing.data_visualizer.print_json"
            ) as mock_print_json:

                # Create a simple mock dictionary
                mock_dict = {"test": "data"}
                mock_namespace_to_dict.return_value = mock_dict
                mock_dumps.return_value = '{"test": "data"}'

                visualizer.print_json_data(test_data)

                # Verify namespace_to_dict was called
                mock_namespace_to_dict.assert_called_once_with(test_data)

                # Verify json.dumps was called with correct arguments
                mock_dumps.assert_called_once_with(mock_dict, indent=4)

                # Verify print_json was called
                mock_print_json.assert_called_once_with(mock_dumps.return_value)

    def test_print_schema_json_serialization_error(self):
        """Test print_schema handles non-serializable schema gracefully."""
        visualizer = DataVisualizer()

        # Create a schema with non-serializable content
        non_serializable_schema = {"type": "object", "properties": {"test": "value"}}

        with patch("hflav_zenodo.processing.data_visualizer.json.dumps") as mock_dumps:
            mock_dumps.side_effect = TypeError("Not JSON serializable")

            # Should raise the exception
            with pytest.raises(TypeError):
                visualizer.print_schema(non_serializable_schema)

    def test_print_json_data_conversion_error(self):
        """Test print_json_data handles namespace conversion errors."""
        visualizer = DataVisualizer()

        test_data = SimpleNamespace(name="test")

        with patch(
            "hflav_zenodo.processing.data_visualizer.namespace_to_dict"
        ) as mock_namespace_to_dict:
            mock_namespace_to_dict.side_effect = Exception("Conversion failed")

            # Should propagate the exception
            with pytest.raises(Exception, match="Conversion failed"):
                visualizer.print_json_data(test_data)

    def test_print_schema_output_format(self):
        """Test that print_schema outputs JSON format."""
        visualizer = DataVisualizer()

        test_schema = {
            "title": "Test Schema",
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string", "description": "User's name"}},
        }

        # Use a simple string for the mock return
        mock_json_string = "mock_json_string"

        with patch(
            "hflav_zenodo.processing.data_visualizer.json.dumps"
        ) as mock_dumps, patch(
            "hflav_zenodo.processing.data_visualizer.print_json"
        ) as mock_print_json:

            mock_dumps.return_value = mock_json_string

            visualizer.print_schema(test_schema)

            # Verify json.dumps was called with the schema
            mock_dumps.assert_called_once_with(test_schema)

            # Verify print_json was called with the expected JSON
            mock_print_json.assert_called_once_with(mock_json_string)

    def test_print_json_data_output_format(self):
        """Test that print_json_data outputs formatted JSON."""
        visualizer = DataVisualizer()

        # Create test data
        test_data = SimpleNamespace(
            id=1, name="Test User", active=True, tags=["python", "testing"]
        )

        with patch(
            "hflav_zenodo.processing.data_visualizer.namespace_to_dict"
        ) as mock_namespace_to_dict, patch(
            "hflav_zenodo.processing.data_visualizer.json.dumps"
        ) as mock_dumps, patch(
            "hflav_zenodo.processing.data_visualizer.print_json"
        ) as mock_print_json:

            # Setup mock returns
            mock_dict = {
                "id": 1,
                "name": "Test User",
                "active": True,
                "tags": ["python", "testing"],
            }
            mock_namespace_to_dict.return_value = mock_dict

            formatted_json = '{\n    "id": 1,\n    "name": "Test User"\n}'
            mock_dumps.return_value = formatted_json

            visualizer.print_json_data(test_data)

            # Verify json.dumps was called with correct arguments
            mock_dumps.assert_called_once_with(mock_dict, indent=4)

            # Verify print_json received the formatted JSON
            mock_print_json.assert_called_once_with(formatted_json)

    def test_methods_return_none(self):
        """Test that both interface methods return None as specified."""
        visualizer = DataVisualizer()

        with patch("hflav_zenodo.processing.data_visualizer.print_json"):
            with patch("hflav_zenodo.processing.data_visualizer.json.dumps"):
                # Test print_schema returns None
                result = visualizer.print_schema({})
                assert result is None

        with patch("hflav_zenodo.processing.data_visualizer.namespace_to_dict"):
            with patch("hflav_zenodo.processing.data_visualizer.json.dumps"):
                with patch("hflav_zenodo.processing.data_visualizer.print_json"):
                    # Test print_json_data returns None
                    result = visualizer.print_json_data(SimpleNamespace())
                    assert result is None

    def test_interface_abstract_methods(self):
        """Test that VisualizerInterface properly defines abstract methods."""
        # This tests the interface itself
        assert hasattr(VisualizerInterface, "print_schema")
        assert hasattr(VisualizerInterface, "print_json_data")

        # Check they are abstract methods
        method = VisualizerInterface.print_schema
        assert getattr(method, "__isabstractmethod__", False) is True

        method = VisualizerInterface.print_json_data
        assert getattr(method, "__isabstractmethod__", False) is True

        # Verify we cannot instantiate the interface directly
        with pytest.raises(TypeError):
            VisualizerInterface()
