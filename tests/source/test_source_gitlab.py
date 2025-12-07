import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from gitlab import GitlabGetError

from hflav_zenodo.source.source_gitlab_client import SourceGitlabClient
from hflav_zenodo.exceptions.source_exceptions import (
    NoSchemaFoundInsideGitlabRepository,
    NoVersionTagFound,
)


class TestSourceGitlab:
    """Test suite for SourceGitlabClient focusing on public interface."""

    @pytest.fixture
    def mock_gitlab_project(self):
        """Mock GitLab project with all necessary components."""
        project = Mock()

        # Mock the tags API
        mock_tag = Mock()
        mock_tag.name = "v1.0.0"
        project.tags = Mock()

        # Mock the files API
        project.files = Mock()

        # Mock the repository tree
        project.repository_tree = Mock()

        return project

    @pytest.fixture
    def mock_gitlab(self):
        """Mock GitLab instance."""
        with patch(
            "hflav_zenodo.source.source_gitlab_client.Gitlab"
        ) as mock_gitlab_class:
            mock_instance = Mock()
            mock_instance.projects = Mock()
            yield mock_gitlab_class, mock_instance

    @pytest.fixture
    def gitlab_client(self, mock_gitlab):
        """Create SourceGitlabClient instance with mocked GitLab."""
        mock_gitlab_class, mock_instance = mock_gitlab

        # Setup the mock project
        mock_project = Mock()
        mock_tag = Mock()
        mock_tag.name = "v1.0.0"
        mock_project.tags = Mock()
        mock_project.tags.get = Mock(return_value=mock_tag)
        mock_project.files = Mock()
        mock_project.repository_tree = Mock()

        mock_instance.projects.get.return_value = mock_project

        return SourceGitlabClient()

    @pytest.fixture
    def sample_schema_content(self):
        """Sample schema JSON content."""
        return json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"name": {"type": "string"}, "value": {"type": "number"}},
            }
        )

    # Test get_schema_inside_repository method - PUBLIC METHOD
    def test_get_schema_inside_repository_success(
        self, gitlab_client, sample_schema_content
    ):
        """Test successful retrieval of schema from repository."""
        # Get the mocked project from the client
        project = gitlab_client.project

        # Setup the full flow
        # 1. Mock tag lookup
        mock_tag = Mock()
        mock_tag.name = "v1.0.0"
        project.tags.get.return_value = mock_tag

        # 2. Mock repository_tree behavior for _search_schema
        mock_schema_file = {
            "type": "blob",
            "name": "template.schema",
            "path": "template.schema",  # Path más simple
        }

        # Simular el comportamiento de _search_schema
        # Primera llamada: encuentra el schema inmediatamente
        project.repository_tree.return_value = [mock_schema_file]

        # 3. Mock file content
        mock_file = Mock()
        mock_file.decode.return_value = sample_schema_content
        project.files.get.return_value = mock_file

        # Execute method
        result = gitlab_client.get_schema_inside_repository("v1.0.0")

        # Verify interactions - repository_tree debe ser llamado al menos una vez
        project.repository_tree.assert_called()

        # files.get should be called with correct arguments
        project.files.get.assert_called_once_with(
            file_path="template.schema", ref="v1.0.0"
        )

        # Verify result
        assert isinstance(result, dict)
        assert result["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert result["type"] == "object"
        assert "properties" in result

    def test_get_schema_inside_repository_default_tag(
        self, gitlab_client, sample_schema_content
    ):
        """Test retrieval of schema with default tag (main)."""
        project = gitlab_client.project

        # Override the tag mock for this test
        mock_tag = Mock()
        mock_tag.name = "main"
        project.tags.get.return_value = mock_tag

        # Setup repository tree and file content
        mock_schema_file = {
            "type": "blob",
            "name": "template.schema",
            "path": "path/to/template.schema",
        }
        project.repository_tree.return_value = [mock_schema_file]

        mock_file = Mock()
        mock_file.decode.return_value = sample_schema_content
        project.files.get.return_value = mock_file

        # Execute method with default parameter
        result = gitlab_client.get_schema_inside_repository()

        # Verify default tag was used
        project.tags.get.assert_called_once_with("main")
        project.files.get.assert_called_once_with(
            file_path="path/to/template.schema", ref="main"
        )

        assert isinstance(result, dict)

    def test_get_schema_inside_repository_tag_not_found(self, gitlab_client):
        """Test retrieval when specified tag does not exist."""
        project = gitlab_client.project

        # Setup tag lookup to fail
        project.tags.get.side_effect = GitlabGetError("404 Tag Not Found", 404)

        # Mock _search_schema to return a valid schema file
        # (esto se ejecutará ANTES de que falle el tag, por eso necesitamos mockearlo)
        mock_schema_file = {
            "type": "blob",
            "name": "template.schema",
            "path": "template.schema",
        }

        with patch.object(
            gitlab_client, "_search_schema", return_value=mock_schema_file
        ):
            with pytest.raises(NoVersionTagFound) as exc_info:
                gitlab_client.get_schema_inside_repository("nonexistent-tag")

            assert "Tag 'nonexistent-tag' not found" in str(exc_info.value)
            project.tags.get.assert_called_once_with("nonexistent-tag")

    def test_get_schema_inside_repository_no_schema_found(self, gitlab_client):
        """Test retrieval when no schema file is found in repository."""
        # Mockear _search_schema para que lance NoSchemaFoundInsideGitlabRepository directamente
        with patch.object(gitlab_client, "_search_schema") as mock_search:
            mock_search.side_effect = NoSchemaFoundInsideGitlabRepository(
                message="No schema found inside the GitLab repository",
                details="No .schema files found",
            )

            with pytest.raises(NoSchemaFoundInsideGitlabRepository) as exc_info:
                gitlab_client.get_schema_inside_repository("v1.0.0")

            assert "No schema found inside the GitLab repository" in str(exc_info.value)
            mock_search.assert_called_once_with("")

    def test_get_schema_inside_repository_nested_schema_search(
        self, gitlab_client, sample_schema_content
    ):
        """Test retrieval when schema is in nested directory."""
        project = gitlab_client.project

        # Setup recursive search behavior
        mock_schema_file = {
            "type": "blob",
            "name": "template.schema",
            "path": "templates/subdir/template.schema",
        }

        # First call returns a directory, second call returns the schema file
        project.repository_tree.side_effect = [
            [{"type": "tree", "name": "templates", "path": "templates"}],
            [mock_schema_file],
        ]

        mock_file = Mock()
        mock_file.decode.return_value = sample_schema_content
        project.files.get.return_value = mock_file

        result = gitlab_client.get_schema_inside_repository("v1.0.0")

        # Verify recursive search was performed
        assert project.repository_tree.call_count == 2
        project.repository_tree.assert_any_call(path="", recursive=False)
        project.repository_tree.assert_any_call(path="templates", recursive=False)

        assert isinstance(result, dict)

    def test_get_schema_inside_repository_invalid_json(self, gitlab_client):
        """Test retrieval when schema file contains invalid JSON."""
        project = gitlab_client.project

        mock_schema_file = {
            "type": "blob",
            "name": "template.schema",
            "path": "template.schema",
        }
        project.repository_tree.return_value = [mock_schema_file]

        mock_file = Mock()
        mock_file.decode.return_value = "invalid json content"
        project.files.get.return_value = mock_file

        with pytest.raises(ValueError) as exc_info:
            gitlab_client.get_schema_inside_repository("v1.0.0")

        assert "Invalid JSON in schema file" in str(exc_info.value)

    def test_get_schema_inside_repository_schema_in_root(
        self, gitlab_client, sample_schema_content
    ):
        """Test retrieval when schema is in root directory."""
        project = gitlab_client.project

        # Mock schema file in root directory
        schema_file = {"type": "blob", "name": "data.schema", "path": "data.schema"}

        project.repository_tree.return_value = [schema_file]

        mock_file = Mock()
        mock_file.decode.return_value = sample_schema_content
        project.files.get.return_value = mock_file

        # Make sure tag.get is mocked correctly
        mock_tag = Mock()
        mock_tag.name = "v1.0.0"
        project.tags.get.return_value = mock_tag

        result = gitlab_client.get_schema_inside_repository("v1.0.0")

        project.files.get.assert_called_once_with(file_path="data.schema", ref="v1.0.0")

        assert isinstance(result, dict)

    def test_get_schema_inside_repository_multiple_schema_files(
        self, gitlab_client, sample_schema_content
    ):
        """Test retrieval when multiple schema files exist (should find first one)."""
        project = gitlab_client.project

        # Configurar que se encuentre algún schema (no importa cuál)
        mock_schema_file = {
            "type": "blob",
            "name": "some.schema",
            "path": "some.schema",
        }

        with patch.object(
            gitlab_client, "_search_schema", return_value=mock_schema_file
        ):
            mock_file = Mock()
            mock_file.decode.return_value = sample_schema_content
            project.files.get.return_value = mock_file

            result = gitlab_client.get_schema_inside_repository("v1.0.0")

            # Verificar que se obtuvo algún schema
            project.files.get.assert_called_once()
            assert isinstance(result, dict)

    def test_get_schema_inside_repository_empty_schema_file(self, gitlab_client):
        """Test retrieval when schema file is empty."""
        project = gitlab_client.project

        mock_schema_file = {
            "type": "blob",
            "name": "template.schema",
            "path": "template.schema",
        }
        project.repository_tree.return_value = [mock_schema_file]

        mock_file = Mock()
        mock_file.decode.return_value = ""
        project.files.get.return_value = mock_file

        with pytest.raises(ValueError) as exc_info:
            gitlab_client.get_schema_inside_repository("v1.0.0")

        assert "Invalid JSON in schema file" in str(exc_info.value)

    def test_get_schema_inside_repository_with_special_characters(
        self, gitlab_client, sample_schema_content
    ):
        """Test retrieval with special characters in tag name."""
        project = gitlab_client.project

        schema_file = {
            "type": "blob",
            "name": "template-v2.schema",
            "path": "templates/v2/template.schema",
        }

        project.repository_tree.return_value = [schema_file]

        mock_file = Mock()
        mock_file.decode.return_value = sample_schema_content
        project.files.get.return_value = mock_file

        # Setup tag with special characters
        mock_tag = Mock()
        mock_tag.name = "release/v1.2.3"
        project.tags.get.return_value = mock_tag

        result = gitlab_client.get_schema_inside_repository("release/v1.2.3")

        project.tags.get.assert_called_once_with("release/v1.2.3")
        project.files.get.assert_called_once_with(
            file_path="templates/v2/template.schema", ref="release/v1.2.3"
        )

        assert isinstance(result, dict)

    def test_get_schema_inside_repository_bytes_content(self, gitlab_client):
        """Test retrieval when file content is returned as bytes."""
        project = gitlab_client.project

        schema_dict = {"type": "object", "properties": {}}
        schema_bytes = json.dumps(schema_dict).encode("utf-8")

        mock_schema_file = {
            "type": "blob",
            "name": "template.schema",
            "path": "template.schema",
        }
        project.repository_tree.return_value = [mock_schema_file]

        mock_file = Mock()
        mock_file.decode.return_value = schema_bytes
        project.files.get.return_value = mock_file

        result = gitlab_client.get_schema_inside_repository("v1.0.0")

        assert isinstance(result, dict)
        assert result == schema_dict

    def test_get_schema_inside_repository_recursive_search_exception(
        self, gitlab_client
    ):
        """Test retrieval when recursive search raises an exception."""
        with patch.object(gitlab_client, "_search_schema") as mock_search:
            # Mock _search_schema para que lance la excepción que espera get_schema_inside_repository
            mock_search.side_effect = NoSchemaFoundInsideGitlabRepository(
                message="No schema found inside the GitLab repository",
                details="Search failed",
            )

            with pytest.raises(NoSchemaFoundInsideGitlabRepository) as exc_info:
                gitlab_client.get_schema_inside_repository("v1.0.0")

            assert "No schema found inside the GitLab repository" in str(exc_info.value)
            mock_search.assert_called_once_with("")

    def test_get_schema_inside_repository_with_branch_ref(self, gitlab_client):
        """Test retrieval using a branch reference instead of tag."""
        project = gitlab_client.project

        # Mock _search_schema para devolver un schema válido
        # (esto se ejecuta ANTES de _get_tag_name)
        mock_schema_file = {
            "type": "blob",
            "name": "template.schema",
            "path": "template.schema",
        }

        with patch.object(
            gitlab_client, "_search_schema", return_value=mock_schema_file
        ):
            # Configurar que _get_tag_name (llamado internamente) falle
            # ya que "feature-branch" no es un tag válido
            project.tags.get.side_effect = GitlabGetError("404 Tag Not Found", 404)

            with pytest.raises(NoVersionTagFound) as exc_info:
                gitlab_client.get_schema_inside_repository("feature-branch")

            assert "Tag 'feature-branch' not found" in str(exc_info.value)
            project.tags.get.assert_called_once_with("feature-branch")
