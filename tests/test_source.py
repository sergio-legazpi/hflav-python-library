import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os
import tempfile

from hflav_zenodo.models.models import Record, Template
from hflav_zenodo.source.source_interface import SourceInterface
from hflav_zenodo.source.source_zenodo_requests import SourceZenodoRequest


class TestSource:
    """Test suite for SourceZenodoRequest class."""

    @pytest.fixture
    def zenodo_client(self) -> SourceInterface:
        return SourceZenodoRequest()

    @pytest.fixture
    def mock_record_data(self):
        return {
            "id": 12345,
            "doi": "10.1234/zenodo.12345",
            "created": "2023-01-01T12:00:00.000000",
            "updated": "2023-01-01T12:00:00.000000",
            "metadata": {"title": "Test Record", "description": "Test description"},
            "files": [
                {
                    "id": "file-1",
                    "key": "test_file.txt",
                    "size": 1024,
                    "type": "txt",
                    "links": {"self": "https://zenodo.org/files/test_file.txt"},
                }
            ],
            "links": {"self": "https://zenodo.org/records/12345"},
        }

    @pytest.fixture
    def mock_template_data(self):
        return {
            "id": 12087576,
            "created": "2023-01-01T12:00:00.000000",
            "updated": "2023-01-01T12:00:00.000000",
            "metadata": {
                "title": "Template Record",
                "description": "Template description",
                "version": "1.0",
            },
            "files": [],
            "links": {"self": "https://zenodo.org/records/12087576"},
        }

    @pytest.fixture
    def mock_search_response(self, mock_record_data):
        return {"hits": {"hits": [mock_record_data], "total": 1}}

    @pytest.fixture
    def mock_versions_response(self, mock_template_data):
        return {
            "hits": {
                "hits": [
                    {
                        **mock_template_data,
                        "id": 12087576,
                        "created": "2023-01-01T12:00:00.000000",
                    },
                    {
                        **mock_template_data,
                        "id": 12087577,
                        "created": "2023-02-01T12:00:00.000000",
                    },
                    {
                        **mock_template_data,
                        "id": 12087578,
                        "created": "2023-03-01T12:00:00.000000",
                    },
                ]
            }
        }

    def test_get_records_by_name_success(self, zenodo_client, mock_search_response):
        """Test successful record search by name."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_search_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            results = zenodo_client.get_records_by_name(query="test", size=10, page=1)

            # Verify request was made with correct parameters
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert "https://zenodo.org/api/records" in args[0]
            assert kwargs["params"]["q"] == "test"
            assert kwargs["params"]["size"] == 10
            assert kwargs["params"]["page"] == 1
            assert kwargs["params"]["communities"] == "hflav"

            # Verify results
            assert len(results) == 1
            assert isinstance(results[0], Record)

    def test_get_records_by_name_http_error(self, zenodo_client):
        """Test record search with HTTP error."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "404 Not Found"
            )
            mock_get.return_value = mock_response

            with pytest.raises(requests.exceptions.HTTPError):
                zenodo_client.get_records_by_name(query="test")

    def test_get_records_by_name_no_hits(self, zenodo_client):
        """Test record search with no results."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"hits": {"hits": []}}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            results = zenodo_client.get_records_by_name(query="nonexistent")

            assert len(results) == 0

    def test_get_record_success(self, zenodo_client, mock_record_data):
        """Test successful record retrieval by ID."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_record_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            record = zenodo_client.get_record(12345)

            mock_get.assert_called_once_with(
                "https://zenodo.org/api/records/12345", timeout=30
            )
            assert isinstance(record, Record)
            assert record.id == 12345

    def test_get_record_http_error(self, zenodo_client):
        """Test record retrieval with HTTP error."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "404 Not Found"
            )
            mock_get.return_value = mock_response

            with pytest.raises(requests.exceptions.HTTPError):
                zenodo_client.get_record(99999)

    def test_get_all_template_versions_success(
        self, zenodo_client, mock_template_data, mock_versions_response
    ):
        """Test successful retrieval of all template versions."""
        with patch("requests.get") as mock_get:
            # Mock the initial record request
            mock_record_response = Mock()
            mock_record_response.json.return_value = {
                "links": {
                    "versions": "https://zenodo.org/api/records/12087575/versions"
                }
            }
            mock_record_response.raise_for_status.return_value = None

            # Mock the versions request
            mock_versions_response_obj = Mock()
            mock_versions_response_obj.json.return_value = mock_versions_response
            mock_versions_response_obj.raise_for_status.return_value = None

            # Set up side effect for multiple calls
            mock_get.side_effect = [mock_record_response, mock_versions_response_obj]

            templates = zenodo_client._get_all_template_versions()

            assert len(templates) == 3
            assert all(isinstance(t, Template) for t in templates)
            assert mock_get.call_count == 2

    def test_get_all_template_versions_no_versions_link(self, zenodo_client):
        """Test template versions retrieval when no versions link exists."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"links": {}}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="No versions link found"):
                zenodo_client._get_all_template_versions()

    def test_get_correct_template_by_date_latest(self, zenodo_client):
        """Test getting latest template when no date is provided."""
        with patch.object(
            zenodo_client, "_get_all_template_versions"
        ) as mock_get_versions:
            # Create templates with different creation dates
            templates = [
                Template(
                    **{
                        "id": 1,
                        "created": datetime(2023, 1, 1),
                        "updated": "2023-01-01T12:00:00.000000",
                        "metadata": {"title": "Template 1", "version": "1.0"},
                        "files": [
                            {
                                "id": "file-1",
                                "key": "template",
                                "size": 1024,
                                "type": "txt",
                                "links": {
                                    "self": "https://zenodo.org/files/template.json"
                                },
                            }
                        ],
                        "links": {},
                    }
                ),
                Template(
                    **{
                        "id": 2,
                        "created": datetime(2023, 3, 1),
                        "updated": "2023-03-01T12:00:00.000000",
                        "metadata": {"title": "Template 2", "version": "2.0"},
                        "files": [
                            {
                                "id": "file-2",
                                "key": "template",
                                "size": 1024,
                                "type": "txt",
                                "links": {
                                    "self": "https://zenodo.org/files/template.json"
                                },
                            }
                        ],
                        "links": {},
                    }
                ),
                Template(
                    **{
                        "id": 3,
                        "created": datetime(2023, 2, 1),
                        "updated": "2023-02-01T12:00:00.000000",
                        "metadata": {"title": "Template 3", "version": "3.0"},
                        "files": [
                            {
                                "id": "file-3",
                                "key": "template",
                                "size": 1024,
                                "type": "txt",
                                "links": {
                                    "self": "https://zenodo.org/files/template.json"
                                },
                            }
                        ],
                        "links": {},
                    }
                ),
            ]
            mock_get_versions.return_value = templates

            template = zenodo_client.get_correct_template_by_date()

            # Should return the template with the latest creation date (id=2)
            assert template.rec_id == 2

    def test_get_correct_template_by_date_specific(self, zenodo_client):
        """Test getting template for a specific date."""
        with patch.object(
            zenodo_client, "_get_all_template_versions"
        ) as mock_get_versions:
            templates = [
                Template(
                    **{
                        "id": 1,
                        "created": datetime(2023, 1, 1),
                        "updated": "2023-01-01T12:00:00.000000",
                        "metadata": {"title": "Template 1", "version": "1.0"},
                        "files": [
                            {
                                "id": "file-1",
                                "key": "template",
                                "size": 1024,
                                "type": "txt",
                                "links": {
                                    "self": "https://zenodo.org/files/template.json"
                                },
                            }
                        ],
                        "links": {},
                    }
                ),
                Template(
                    **{
                        "id": 2,
                        "created": datetime(2023, 2, 1),
                        "updated": "2023-02-01T12:00:00.000000",
                        "metadata": {"title": "Template 2", "version": "2.0"},
                        "files": [
                            {
                                "id": "file-2",
                                "key": "template",
                                "size": 1024,
                                "type": "txt",
                                "links": {
                                    "self": "https://zenodo.org/files/template.json"
                                },
                            }
                        ],
                        "links": {},
                    }
                ),
                Template(
                    **{
                        "id": 3,
                        "created": datetime(2023, 3, 1),
                        "updated": "2023-03-01T12:00:00.000000",
                        "metadata": {"title": "Template 3", "version": "3.0"},
                        "files": [
                            {
                                "id": "file-3",
                                "key": "template",
                                "size": 1024,
                                "type": "txt",
                                "links": {
                                    "self": "https://zenodo.org/files/template.json"
                                },
                            }
                        ],
                        "links": {},
                    }
                ),
            ]
            mock_get_versions.return_value = templates

            target_date = datetime(2023, 2, 15)
            template = zenodo_client.get_correct_template_by_date(target_date)

            # Should return the latest template before or on Feb 15 (id=2)
            assert template.rec_id == 2

    def test_get_correct_template_by_date_no_valid_templates(self, zenodo_client):
        """Test getting template when no templates exist before the given date."""
        with patch.object(
            zenodo_client, "_get_all_template_versions"
        ) as mock_get_versions:
            templates = [
                Template(
                    **{
                        "id": 1,
                        "created": datetime(2023, 2, 1),
                        "updated": "2023-02-01T12:00:00.000000",
                        "metadata": {"title": "Template 1", "version": "1.0"},
                        "files": [
                            {
                                "id": "file-1",
                                "key": "template",
                                "size": 1024,
                                "type": "txt",
                                "links": {
                                    "self": "https://zenodo.org/files/template.json"
                                },
                            }
                        ],
                        "links": {},
                    }
                )
            ]
            mock_get_versions.return_value = templates

            target_date = datetime(2022, 1, 1)  # Before any template exists

            with pytest.raises(
                ValueError, match="No template versions found before date"
            ):
                zenodo_client.get_correct_template_by_date(target_date)

    def test_download_file_by_id_and_filename_success(
        self, zenodo_client, mock_record_data
    ):
        """Test successful file download by ID and filename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the record retrieval
            with patch.object(zenodo_client, "get_record") as mock_get_record:
                record = Record(**mock_record_data)
                mock_get_record.return_value = record

                # Mock the file download request
                with patch("requests.get") as mock_get:
                    mock_response = Mock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.iter_content.return_value = [b"test file content"]
                    mock_get.return_value = mock_response

                    dest_path = os.path.join(temp_dir, "downloaded_file.txt")
                    result_path = zenodo_client.download_file_by_id_and_filename(
                        id=12345, filename="test_file.txt", dest_path=dest_path
                    )

                    # Verify file was created with correct content
                    assert result_path == dest_path
                    with open(result_path, "rb") as f:
                        assert f.read() == b"test file content"

                    # Verify download URL was called
                    mock_get.assert_called_once_with(
                        "https://zenodo.org/files/test_file.txt",
                        stream=True,
                        timeout=60,
                    )

    def test_download_file_by_id_and_filename_no_download_url(
        self, zenodo_client, mock_record_data
    ):
        """Test file download when no download URL is available."""
        # Modify record data to remove download link
        broken_record_data = mock_record_data.copy()
        broken_record_data["files"][0]["links"]["download"] = None

        with patch.object(zenodo_client, "get_record") as mock_get_record:
            record = Record(**broken_record_data)
            mock_get_record.return_value = record

            with pytest.raises(requests.exceptions.HTTPError):
                zenodo_client.download_file_by_id_and_filename(id=12345)

    def test_download_file_by_id_and_filename_download_error(
        self, zenodo_client, mock_record_data
    ):
        """Test file download when HTTP error occurs during download."""
        with patch.object(zenodo_client, "get_record") as mock_get_record:
            record = Record(**mock_record_data)
            mock_get_record.return_value = record

            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_response.raise_for_status.side_effect = (
                    requests.exceptions.HTTPError("Download failed")
                )
                mock_get.return_value = mock_response

                with pytest.raises(requests.exceptions.HTTPError):
                    zenodo_client.download_file_by_id_and_filename(id=12345)

    def test_download_file_by_id_and_filename_default_filename(
        self, zenodo_client, mock_record_data
    ):
        """Test file download using default filename when none specified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(zenodo_client, "get_record") as mock_get_record:
                record = Record(**mock_record_data)
                mock_get_record.return_value = record

                with patch("requests.get") as mock_get:
                    mock_response = Mock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.iter_content.return_value = [b"content"]
                    mock_get.return_value = mock_response

                    # Don't specify filename, should use first file
                    result_path = zenodo_client.download_file_by_id_and_filename(
                        id=12345, dest_path=temp_dir
                    )

                    # Should create file with the record's filename
                    expected_path = os.path.join(temp_dir, "test_file.txt")
                    assert result_path == expected_path

    def test_download_file_by_id_and_filename_invalid_id_type(self, zenodo_client):
        """Test file download with invalid ID type."""
        with pytest.raises(ValueError, match="record_or_id must be an int"):
            zenodo_client.download_file_by_id_and_filename(id="invalid")

    def test_record_get_file_by_name(self, mock_record_data):
        """Test Record.get_file_by_name method."""
        record = Record(**mock_record_data)

        # Test finding existing file
        file = record.get_file_by_name("test_file.txt")
        assert file is not None
        assert file.name == "test_file.txt"

        # Test finding non-existent file
        with pytest.raises(
            ValueError,
            match=f"File with name nonexistent.txt not found in record {record.id}",
        ):
            record.get_file_by_name("nonexistent.txt")
