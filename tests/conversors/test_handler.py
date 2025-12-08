import pytest
import json
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, patch, create_autospec
from pathlib import Path

from hflav_zenodo.conversors.conversor_handler import ConversorHandler
from hflav_zenodo.conversors.conversor_interface import ConversorInterface
from hflav_zenodo.processing.visualizer_interface import VisualizerInterface
from hflav_zenodo.source.source_interface import SourceInterface
from hflav_zenodo.source.source_gitlab_interface import SourceGitlabInterface
from hflav_zenodo.models.models import Template, File

from hflav_zenodo.conversors.gitlab_schema_handler import GitlabSchemaHandler
from hflav_zenodo.conversors.template_schema_handler import TemplateSchemaHandler
from hflav_zenodo.conversors.zenodo_schema_handler import ZenodoSchemaHandler


class TestConversorHandler:
    """Tests for ConversorHandler abstract base class."""

    def test_conversor_handler_is_abstract(self):
        """Test that ConversorHandler cannot be instantiated directly."""
        with pytest.raises(TypeError):
            handler = ConversorHandler()

    def test_conversor_handler_has_required_methods(self):
        """Test that ConversorHandler defines required abstract methods."""
        assert hasattr(ConversorHandler, "handle")
        assert hasattr(ConversorHandler, "can_handle")
        assert hasattr(ConversorHandler, "set_next")


class TestZenodoSchemaHandler:
    """Tests for ZenodoSchemaHandler class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for handlers."""
        return {
            "source": Mock(spec=SourceInterface),
            "conversor": Mock(spec=ConversorInterface),
            "visualizer": Mock(spec=VisualizerInterface),
        }

    @pytest.fixture
    def mock_template_with_schema(self):
        """Create a mock template with JSON schema."""
        template = Mock(spec=Template)
        template.rec_id = 12345
        template.jsonschema = Mock(spec=File)
        template.jsonschema.name = "schema.json"
        template.jsontemplate = Mock(spec=File)
        return template

    @pytest.fixture
    def mock_template_without_schema(self):
        """Create a mock template without JSON schema."""
        template = Mock(spec=Template)
        template.jsonschema = None
        template.jsontemplate = Mock(spec=File)
        return template

    def test_zenodo_schema_handler_initialization(self, mock_dependencies):
        """Test ZenodoSchemaHandler initialization."""
        # Patch the inject decorator at the module where it's used (conversor_handler)
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = ZenodoSchemaHandler(
                source=mock_dependencies["source"],
                conversor=mock_dependencies["conversor"],
                visualizer=mock_dependencies["visualizer"],
            )

            assert isinstance(handler, ConversorHandler)
            assert handler._source == mock_dependencies["source"]
            assert handler._conversor == mock_dependencies["conversor"]
            assert handler._visualizer == mock_dependencies["visualizer"]

    def test_zenodo_schema_handler_can_handle_with_schema(
        self, mock_dependencies, mock_template_with_schema
    ):
        """Test can_handle returns True when template has JSON schema."""
        # Patch the inject decorator
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = ZenodoSchemaHandler(**mock_dependencies)
            data_path = "/path/to/data.json"

            result = handler.can_handle(mock_template_with_schema, data_path)

            # template.jsonschema is a Mock object, which should evaluate to True
            assert result == mock_template_with_schema.jsonschema

    def test_zenodo_schema_handler_can_handle_without_schema(
        self, mock_dependencies, mock_template_without_schema
    ):
        """Test can_handle returns False when template has no JSON schema."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = ZenodoSchemaHandler(**mock_dependencies)
            data_path = "/path/to/data.json"

            result = handler.can_handle(mock_template_without_schema, data_path)

            assert result is None

    def test_zenodo_schema_handler_set_next(self, mock_dependencies):
        """Test set_next method sets next handler."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = ZenodoSchemaHandler(**mock_dependencies)
            next_handler = Mock(spec=ConversorHandler)

            result = handler.set_next(next_handler)

            assert hasattr(handler, "_next_handler")
            assert handler._next_handler == next_handler
            assert result == next_handler

    def test_zenodo_schema_handler_handle_with_schema(
        self, mock_dependencies, mock_template_with_schema
    ):
        """Test handle method when template has JSON schema."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            # Setup mocks
            schema_path = "/tmp/schema.json"
            schema_content = {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            }
            data_path = "/path/to/data.json"
            expected_result = SimpleNamespace(name="test")

            mock_dependencies[
                "source"
            ].download_file_by_id_and_filename.return_value = schema_path
            mock_dependencies[
                "conversor"
            ].generate_instance_from_schema_and_data.return_value = expected_result

            # Create handler
            handler = ZenodoSchemaHandler(**mock_dependencies)

            # Mock open and json.load
            mock_file = Mock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)

            with patch("builtins.open", return_value=mock_file):
                with patch("json.load", return_value=schema_content):
                    result = handler.handle(mock_template_with_schema, data_path)

            # Verify calls
            mock_dependencies[
                "source"
            ].download_file_by_id_and_filename.assert_called_once_with(
                id=12345, filename="schema.json"
            )
            mock_dependencies[
                "conversor"
            ].generate_instance_from_schema_and_data.assert_called_once_with(
                schema_content, data_path
            )
            assert result == expected_result

    def test_zenodo_schema_handler_handle_without_schema(
        self, mock_dependencies, mock_template_without_schema
    ):
        """Test handle method when template has no JSON schema (passes to next)."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            # Setup handler chain
            handler = ZenodoSchemaHandler(**mock_dependencies)
            next_handler = Mock(spec=ConversorHandler)
            expected_result = SimpleNamespace(name="from_next")
            next_handler.handle.return_value = expected_result
            handler.set_next(next_handler)

            data_path = "/path/to/data.json"

            result = handler.handle(mock_template_without_schema, data_path)

            # Should call next handler
            next_handler.handle.assert_called_once_with(
                mock_template_without_schema, data_path
            )
            assert result == expected_result


class TestGitlabSchemaHandler:
    """Tests for GitlabSchemaHandler class."""

    @pytest.fixture
    def mock_dependencies_with_gitlab(self):
        """Create mock dependencies including gitlab_source."""
        return {
            "source": Mock(spec=SourceInterface),
            "conversor": Mock(spec=ConversorInterface),
            "visualizer": Mock(spec=VisualizerInterface),
            "gitlab_source": Mock(spec=SourceGitlabInterface),
        }

    @pytest.fixture
    def mock_template_with_json_template(self):
        """Create a mock template with JSON template."""
        template = Mock(spec=Template)
        template.jsonschema = None
        template.jsontemplate = Mock(spec=File)
        return template

    @pytest.fixture
    def mock_template_without_json_template(self):
        """Create a mock template without JSON template."""
        template = Mock(spec=Template)
        template.jsonschema = None
        template.jsontemplate = None
        return template

    def test_gitlab_schema_handler_initialization(self, mock_dependencies_with_gitlab):
        """Test GitlabSchemaHandler initialization with gitlab source."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = GitlabSchemaHandler(
                source=mock_dependencies_with_gitlab["source"],
                conversor=mock_dependencies_with_gitlab["conversor"],
                visualizer=mock_dependencies_with_gitlab["visualizer"],
                gitlab_source=mock_dependencies_with_gitlab["gitlab_source"],
            )

            assert isinstance(handler, ConversorHandler)
            assert handler._source == mock_dependencies_with_gitlab["source"]
            assert handler._conversor == mock_dependencies_with_gitlab["conversor"]
            assert handler._visualizer == mock_dependencies_with_gitlab["visualizer"]
            assert (
                handler._source_gitlab_client
                == mock_dependencies_with_gitlab["gitlab_source"]
            )

    def test_gitlab_schema_handler_can_handle_with_template(
        self, mock_dependencies_with_gitlab, mock_template_with_json_template
    ):
        """Test can_handle returns True when template has JSON template."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = GitlabSchemaHandler(**mock_dependencies_with_gitlab)
            data_path = "/path/to/data.json"

            result = handler.can_handle(mock_template_with_json_template, data_path)

            # template.jsontemplate is a Mock object
            assert result == mock_template_with_json_template.jsontemplate

    def test_gitlab_schema_handler_can_handle_without_template(
        self, mock_dependencies_with_gitlab, mock_template_without_json_template
    ):
        """Test can_handle returns False when template has no JSON template."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = GitlabSchemaHandler(**mock_dependencies_with_gitlab)
            data_path = "/path/to/data.json"

            result = handler.can_handle(mock_template_without_json_template, data_path)

            assert result is None

    def test_gitlab_schema_handler_set_next(self, mock_dependencies_with_gitlab):
        """Test set_next method sets next handler."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = GitlabSchemaHandler(**mock_dependencies_with_gitlab)
            next_handler = Mock(spec=ConversorHandler)

            result = handler.set_next(next_handler)

            assert hasattr(handler, "_next_handler")
            assert handler._next_handler == next_handler
            assert result == next_handler

    def test_try_to_get_schema_version_found(self, mock_dependencies_with_gitlab):
        """Test _try_to_get_schema_version when schema version is found."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = GitlabSchemaHandler(**mock_dependencies_with_gitlab)

            # Create a temporary file with schema version
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                f.write('{\n  "schema": "v1.0.0"\n}')
                temp_path = f.name

            try:
                version = handler._try_to_get_schema_version(temp_path)
                assert version == "v1.0.0"
            finally:
                Path(temp_path).unlink()

    def test_try_to_get_schema_version_not_found(self, mock_dependencies_with_gitlab):
        """Test _try_to_get_schema_version when schema version is not found."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = GitlabSchemaHandler(**mock_dependencies_with_gitlab)

            # Create a temporary file without schema version
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                f.write('{\n  "name": "test"\n}')
                temp_path = f.name

            try:
                version = handler._try_to_get_schema_version(temp_path)
                assert version == "main"  # Default
            finally:
                Path(temp_path).unlink()

    def test_gitlab_schema_handler_handle_success(
        self, mock_dependencies_with_gitlab, mock_template_with_json_template
    ):
        """Test handle method when gitlab schema retrieval succeeds."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            # Setup mocks
            data_path = "/path/to/data.json"
            schema_dict = {"type": "object", "properties": {"name": {"type": "string"}}}
            expected_result = SimpleNamespace(name="test")

            handler = GitlabSchemaHandler(**mock_dependencies_with_gitlab)

            # Mock _try_to_get_schema_version
            handler._try_to_get_schema_version = Mock(return_value="v1.0.0")

            # Mock gitlab source
            mock_dependencies_with_gitlab[
                "gitlab_source"
            ].get_schema_inside_repository.return_value = schema_dict

            # Mock conversor
            mock_dependencies_with_gitlab[
                "conversor"
            ].generate_instance_from_schema_and_data.return_value = expected_result

            result = handler.handle(mock_template_with_json_template, data_path)

            # Verify calls
            handler._try_to_get_schema_version.assert_called_once_with(data_path)
            mock_dependencies_with_gitlab[
                "gitlab_source"
            ].get_schema_inside_repository.assert_called_once_with("v1.0.0")
            mock_dependencies_with_gitlab[
                "conversor"
            ].generate_instance_from_schema_and_data.assert_called_once_with(
                schema_dict, data_path
            )
            assert result == expected_result

    def test_gitlab_schema_handler_handle_gitlab_failure(
        self, mock_dependencies_with_gitlab, mock_template_with_json_template
    ):
        """Test handle method when gitlab schema retrieval fails."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            # Setup mocks
            data_path = "/path/to/data.json"

            handler = GitlabSchemaHandler(**mock_dependencies_with_gitlab)
            next_handler = Mock(spec=ConversorHandler)
            expected_result = SimpleNamespace(name="from_next")
            next_handler.handle.return_value = expected_result
            handler.set_next(next_handler)

            # Mock _try_to_get_schema_version
            handler._try_to_get_schema_version = Mock(return_value="v1.0.0")

            # Mock gitlab source to raise exception
            from hflav_zenodo.exceptions.source_exceptions import (
                NoSchemaFoundInsideGitlabRepository,
            )

            mock_dependencies_with_gitlab[
                "gitlab_source"
            ].get_schema_inside_repository.side_effect = NoSchemaFoundInsideGitlabRepository(
                "Not found"
            )

            result = handler.handle(mock_template_with_json_template, data_path)

            # Should call next handler
            next_handler.handle.assert_called_once_with(
                mock_template_with_json_template, data_path
            )
            assert result == expected_result

    def test_gitlab_schema_handler_handle_cannot_handle(
        self, mock_dependencies_with_gitlab, mock_template_without_json_template
    ):
        """Test handle method when cannot handle (passes to next)."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            # Setup handler chain
            handler = GitlabSchemaHandler(**mock_dependencies_with_gitlab)
            next_handler = Mock(spec=ConversorHandler)
            expected_result = SimpleNamespace(name="from_next")
            next_handler.handle.return_value = expected_result
            handler.set_next(next_handler)

            data_path = "/path/to/data.json"

            result = handler.handle(mock_template_without_json_template, data_path)

            # Should call next handler
            next_handler.handle.assert_called_once_with(
                mock_template_without_json_template, data_path
            )
            assert result == expected_result


class TestTemplateSchemaHandler:
    """Tests for TemplateSchemaHandler class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for handlers."""
        return {
            "source": Mock(spec=SourceInterface),
            "conversor": Mock(spec=ConversorInterface),
            "visualizer": Mock(spec=VisualizerInterface),
        }

    @pytest.fixture
    def mock_template_with_json_template(self):
        """Create a mock template with JSON template."""
        template = Mock(spec=Template)
        template.rec_id = 12345
        template.jsonschema = None
        template.jsontemplate = Mock(spec=File)
        template.jsontemplate.name = "template.json"
        return template

    @pytest.fixture
    def mock_template_without_json_template(self):
        """Create a mock template without JSON template."""
        template = Mock(spec=Template)
        template.jsonschema = None
        template.jsontemplate = None
        return template

    def test_template_schema_handler_initialization(self, mock_dependencies):
        """Test TemplateSchemaHandler initialization."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = TemplateSchemaHandler(
                source=mock_dependencies["source"],
                conversor=mock_dependencies["conversor"],
                visualizer=mock_dependencies["visualizer"],
            )

            assert isinstance(handler, ConversorHandler)
            assert handler._source == mock_dependencies["source"]
            assert handler._conversor == mock_dependencies["conversor"]
            assert handler._visualizer == mock_dependencies["visualizer"]

    def test_template_schema_handler_can_handle_with_template(
        self, mock_dependencies, mock_template_with_json_template
    ):
        """Test can_handle returns True when template has JSON template."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = TemplateSchemaHandler(**mock_dependencies)
            data_path = "/path/to/data.json"

            result = handler.can_handle(mock_template_with_json_template, data_path)

            # template.jsontemplate is a Mock object
            assert result == mock_template_with_json_template.jsontemplate

    def test_template_schema_handler_can_handle_without_template(
        self, mock_dependencies, mock_template_without_json_template
    ):
        """Test can_handle returns False when template has no JSON template."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = TemplateSchemaHandler(**mock_dependencies)
            data_path = "/path/to/data.json"

            result = handler.can_handle(mock_template_without_json_template, data_path)

            assert result is None

    def test_template_schema_handler_set_next(self, mock_dependencies):
        """Test set_next method sets next handler."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = TemplateSchemaHandler(**mock_dependencies)
            next_handler = Mock(spec=ConversorHandler)

            result = handler.set_next(next_handler)

            assert hasattr(handler, "_next_handler")
            assert handler._next_handler == next_handler
            assert result == next_handler

    def test_template_schema_handler_handle_success(
        self, mock_dependencies, mock_template_with_json_template
    ):
        """Test handle method when template processing succeeds."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            # Setup mocks
            template_path = "/tmp/template.json"
            data_path = "/path/to/data.json"
            generated_schema = {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            }
            expected_result = SimpleNamespace(name="test")

            mock_dependencies[
                "source"
            ].download_file_by_id_and_filename.return_value = template_path
            mock_dependencies["conversor"].generate_json_schema.return_value = (
                generated_schema
            )
            mock_dependencies[
                "conversor"
            ].generate_instance_from_schema_and_data.return_value = expected_result

            handler = TemplateSchemaHandler(**mock_dependencies)
            result = handler.handle(mock_template_with_json_template, data_path)

            # Verify calls
            mock_dependencies[
                "source"
            ].download_file_by_id_and_filename.assert_called_once_with(
                id=12345, filename="template.json"
            )
            mock_dependencies["conversor"].generate_json_schema.assert_called_once_with(
                template_path
            )
            mock_dependencies[
                "conversor"
            ].generate_instance_from_schema_and_data.assert_called_once_with(
                generated_schema, data_path
            )
            assert result == expected_result

    def test_template_schema_handler_handle_cannot_handle(
        self, mock_dependencies, mock_template_without_json_template
    ):
        """Test handle method when cannot handle (raises exception)."""
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):
            handler = TemplateSchemaHandler(**mock_dependencies)
            data_path = "/path/to/data.json"

            with pytest.raises(
                Exception, match="No handler available for this template and data path"
            ):
                handler.handle(mock_template_without_json_template, data_path)


class TestChainOfResponsibilityIntegration:
    """Integration tests for the Chain of Responsibility pattern."""

    def test_full_handler_chain(self):
        """Test the complete chain of responsibility."""
        # Create mock dependencies
        mock_source = Mock(spec=SourceInterface)
        mock_conversor = Mock(spec=ConversorInterface)
        mock_visualizer = Mock(spec=VisualizerInterface)
        mock_gitlab_source = Mock(spec=SourceGitlabInterface)

        # Create templates
        template_with_schema = Mock(spec=Template)
        template_with_schema.rec_id = 12345
        template_with_schema.jsonschema = Mock(spec=File)
        template_with_schema.jsonschema.name = "schema.json"
        template_with_schema.jsontemplate = Mock(spec=File)

        template_only_template = Mock(spec=Template)
        template_only_template.jsonschema = None
        template_only_template.jsontemplate = Mock(spec=File)

        template_neither = Mock(spec=Template)
        template_neither.jsonschema = None
        template_neither.jsontemplate = Mock(spec=File)

        data_path = "/path/to/data.json"

        # Patch inject decorator at the base class
        with patch("hflav_zenodo.conversors.conversor_handler.inject", lambda x: x):

            # Create handlers
            zenodo_handler = ZenodoSchemaHandler(
                source=mock_source, conversor=mock_conversor, visualizer=mock_visualizer
            )

            gitlab_handler = GitlabSchemaHandler(
                source=mock_source,
                conversor=mock_conversor,
                visualizer=mock_visualizer,
                gitlab_source=mock_gitlab_source,
            )

            template_handler = TemplateSchemaHandler(
                source=mock_source, conversor=mock_conversor, visualizer=mock_visualizer
            )

            # Build the chain
            zenodo_handler.set_next(gitlab_handler).set_next(template_handler)

            # Test 1: Zenodo handler should handle template with schema
            mock_conversor.generate_instance_from_schema_and_data.reset_mock()
            mock_source.download_file_by_id_and_filename.reset_mock()

            # Setup Zenodo handler success
            schema_path = "/tmp/schema.json"
            schema_content = {"type": "object"}
            expected_zenodo_result = SimpleNamespace(name="zenodo_result")

            mock_source.download_file_by_id_and_filename.return_value = schema_path
            mock_conversor.generate_instance_from_schema_and_data.return_value = (
                expected_zenodo_result
            )

            # Mock open and json.load for Zenodo handler
            mock_file = Mock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)

            with patch("builtins.open", return_value=mock_file):
                with patch("json.load", return_value=schema_content):
                    result = zenodo_handler.handle(template_with_schema, data_path)

            assert result == expected_zenodo_result
            mock_source.download_file_by_id_and_filename.assert_called_once_with(
                id=12345, filename="schema.json"
            )

            # Reset for next test
            mock_conversor.generate_instance_from_schema_and_data.reset_mock()
            mock_gitlab_source.get_schema_inside_repository.reset_mock()

            # Test 2: Gitlab handler should handle template with only template
            # Setup Gitlab handler success
            gitlab_schema = {
                "type": "object",
                "properties": {"gitlab": {"type": "string"}},
            }
            expected_gitlab_result = SimpleNamespace(gitlab="result")

            mock_gitlab_source.get_schema_inside_repository.return_value = gitlab_schema
            mock_conversor.generate_instance_from_schema_and_data.return_value = (
                expected_gitlab_result
            )

            # Mock _try_to_get_schema_version
            gitlab_handler._try_to_get_schema_version = Mock(return_value="v1.0.0")

            result = zenodo_handler.handle(template_only_template, data_path)
            assert result == expected_gitlab_result
            mock_gitlab_source.get_schema_inside_repository.assert_called_once_with(
                "v1.0.0"
            )

            # Reset for next test
            mock_conversor.generate_instance_from_schema_and_data.reset_mock()
            mock_conversor.generate_json_schema.reset_mock()
            mock_source.download_file_by_id_and_filename.reset_mock()

            # Test 3: Template handler should handle when others cannot
            # Setup Template handler success
            template_path = "/tmp/template.json"
            generated_schema = {
                "type": "object",
                "properties": {"template": {"type": "string"}},
            }
            expected_template_result = SimpleNamespace(template="result")

            mock_source.download_file_by_id_and_filename.return_value = template_path
            mock_conversor.generate_json_schema.return_value = generated_schema
            mock_conversor.generate_instance_from_schema_and_data.return_value = (
                expected_template_result
            )

            result = zenodo_handler.handle(template_neither, data_path)
            assert result == expected_template_result
