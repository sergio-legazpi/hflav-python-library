import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import tempfile
import os
import requests

from hflav_zenodo.exceptions.source_exceptions import (
    DataAccessException,
    DataNotFoundException,
)
from hflav_zenodo.filters.base_query import BaseQuery
from hflav_zenodo.filters.search_filters import OrFilter, QueryBuilder
from hflav_zenodo.models.models import Record, Template, File
from hflav_zenodo.source.source_zenodo_requests import SourceZenodoRequest


class TestSourceZenodoRequest(unittest.TestCase):
    def setUp(self):
        """Initial setup for each test."""
        self.source = SourceZenodoRequest()
        self.mock_record_data = {
            "id": 123456,
            "created": "2023-01-01T12:00:00.000000",
            "metadata": {"title": "Test Record"},
            "doi": "10.1234/zenodo.123456",
            "updated": "2023-01-02T12:00:00.000000",
            "files": [
                {
                    "key": "test_file.txt",
                    "links": {"download": "http://example.com/download/test_file.txt"},
                    "size": 1024,
                }
            ],
        }
        self.mock_template_data = {
            "id": 789012,
            "created": "2023-01-01T12:00:00.000000",
            "conceptrecid": 12087575,
            "metadata": {"title": "Template Record"},
        }

    def test_initialization(self):
        """Test class initialization."""
        self.assertEqual(self.source.DEFAULT_BASE, "https://zenodo.org/api")
        self.assertEqual(self.source.CONCEPT_ID_TEMPLATE, 12087575)

    @patch("requests.get")
    def test_get_records_by_name_success(self, mock_get):
        """Successful test of get_records_by_name."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "hits": {
                "hits": [
                    {
                        "id": 1,
                        "doi": "10.1234/zenodo.1",
                        "updated": "2023-01-02T12:00:00.000000",
                        "created": "2023-01-01T12:00:00.000000",
                        "metadata": {"title": "Record 1"},
                        "files": [],
                    },
                    {
                        "id": 2,
                        "doi": "10.1234/zenodo.2",
                        "updated": "2023-01-03T12:00:00.000000",
                        "created": "2023-01-02T12:00:00.000000",
                        "metadata": {"title": "Record 2"},
                        "files": [],
                    },
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Mock query
        mock_query = Mock(spec=BaseQuery)
        mock_query.build_params.return_value = {"q": "test"}

        # Execute method
        result = self.source.get_records_by_name(mock_query)

        # Verifications
        mock_get.assert_called_once_with(
            "https://zenodo.org/api/records",
            params={"q": "test"},
            timeout=30,
        )
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Record)
        self.assertIsInstance(result[1], Record)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)

    @patch("requests.get")
    def test_get_records_by_name_http_error(self, mock_get):
        """Test of get_records_by_name with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error")
        mock_get.return_value = mock_response

        mock_query = Mock(spec=BaseQuery)
        mock_query.build_params.return_value = {}

        with self.assertRaises(DataAccessException) as context:
            self.source.get_records_by_name(mock_query)

        self.assertIn("Failed to get records by name", str(context.exception))

    @patch("requests.get")
    def test_get_record_success(self, mock_get):
        """Successful test of get_record."""
        mock_response = Mock()
        mock_response.json.return_value = self.mock_record_data
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.source.get_record(123456)

        mock_get.assert_called_once_with(
            "https://zenodo.org/api/records/123456",
            timeout=30,
        )
        self.assertIsInstance(result, Record)
        self.assertEqual(result.id, 123456)

    @patch("requests.get")
    def test_get_record_invalid_id(self, mock_get):
        """Test of get_record with invalid ID."""
        with self.assertRaises(ValueError):
            self.source.get_record(0)

        with self.assertRaises(ValueError):
            self.source.get_record(None)

    @patch("requests.get")
    def test_get_record_http_error(self, mock_get):
        """Test of get_record with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error")
        mock_get.return_value = mock_response

        with self.assertRaises(DataAccessException) as context:
            self.source.get_record(123456)

        self.assertIn("Failed to get record", str(context.exception))

    @patch.object(SourceZenodoRequest, "_get_all_template_versions")
    def test_get_correct_template_by_date_none(self, mock_get_templates):
        """Test of get_correct_template_by_date without date."""
        # Create templates with different dates
        template1 = Mock(spec=Template)
        template1.created = datetime(2023, 1, 1, tzinfo=timezone.utc)

        template2 = Mock(spec=Template)
        template2.created = datetime(2023, 2, 1, tzinfo=timezone.utc)

        template3 = Mock(spec=Template)
        template3.created = datetime(2023, 3, 1, tzinfo=timezone.utc)

        mock_get_templates.return_value = [template1, template2, template3]

        result = self.source.get_correct_template_by_date()

        # Should return the most recent (template3)
        self.assertEqual(result, template3)
        mock_get_templates.assert_called_once()

    @patch.object(SourceZenodoRequest, "_get_all_template_versions")
    def test_get_correct_template_by_date_with_date(self, mock_get_templates):
        """Test of get_correct_template_by_date with specific date."""
        # Create templates with different dates
        template1 = Mock(spec=Template)
        template1.created = datetime(2023, 1, 1, tzinfo=timezone.utc)

        template2 = Mock(spec=Template)
        template2.created = datetime(2023, 2, 1, tzinfo=timezone.utc)

        template3 = Mock(spec=Template)
        template3.created = datetime(2023, 3, 1, tzinfo=timezone.utc)

        mock_get_templates.return_value = [template1, template2, template3]

        # Date between template2 and template3
        target_date = datetime(2023, 2, 15, tzinfo=timezone.utc)
        result = self.source.get_correct_template_by_date(target_date)

        # Should return the most recent before or on the date (template2)
        self.assertEqual(result, template2)

    @patch.object(SourceZenodoRequest, "_get_all_template_versions")
    def test_get_correct_template_by_date_no_valid_templates(self, mock_get_templates):
        """Test of get_correct_template_by_date without valid templates."""
        template = Mock(spec=Template)
        template.created = datetime(2023, 3, 1, tzinfo=timezone.utc)
        mock_get_templates.return_value = [template]

        # Date before all templates
        target_date = datetime(2022, 1, 1, tzinfo=timezone.utc)

        with self.assertRaises(DataNotFoundException) as context:
            self.source.get_correct_template_by_date(target_date)

        self.assertIn("No template versions found before date", str(context.exception))

    @patch.object(SourceZenodoRequest, "get_record")
    @patch("requests.get")
    def test_download_file_by_id_and_filename_success(self, mock_get, mock_get_record):
        """Successful test of download_file_by_id_and_filename."""
        # Mock record with file
        mock_file = Mock(spec=File)
        mock_file.name = "test_file.txt"
        mock_file.download_url = "http://example.com/download/test_file.txt"

        mock_record = Mock(spec=Record)
        mock_record.id = 123456
        mock_record.get_child.return_value = mock_file

        mock_get_record.return_value = mock_record

        # Mock download response
        mock_response = Mock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2", b"chunk3"]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = self.source.download_file_by_id_and_filename(
                123456, "test_file.txt", temp_dir
            )

            # Verifications
            mock_get_record.assert_called_once_with(123456)
            mock_record.get_child.assert_called_once_with("test_file.txt")
            mock_get.assert_called_once_with(
                "http://example.com/download/test_file.txt",
                stream=True,
                timeout=60,
            )

            # Verify file was created
            self.assertTrue(os.path.exists(result_path))
            self.assertTrue(result_path.startswith(temp_dir))
            self.assertIn("test_file.txt", result_path)

    @patch.object(SourceZenodoRequest, "get_record")
    def test_download_file_by_id_and_filename_invalid_id(self, mock_get_record):
        """Test of download_file_by_id_and_filename with invalid ID."""
        with self.assertRaises(ValueError):
            self.source.download_file_by_id_and_filename(0, "test.txt")

        with self.assertRaises(ValueError):
            self.source.download_file_by_id_and_filename(None, "test.txt")

    @patch.object(SourceZenodoRequest, "get_record")
    def test_download_file_by_id_and_filename_invalid_filename(self, mock_get_record):
        """Test of download_file_by_id_and_filename with invalid filename."""
        mock_record = Mock(spec=Record)
        mock_get_record.return_value = mock_record

        with self.assertRaises(ValueError):
            self.source.download_file_by_id_and_filename(123456, "")

        with self.assertRaises(ValueError):
            self.source.download_file_by_id_and_filename(123456, None)

    @patch.object(SourceZenodoRequest, "get_record")
    def test_download_file_by_id_and_filename_no_download_url(self, mock_get_record):
        """Test of download_file_by_id_and_filename without download URL."""
        mock_file = Mock(spec=File)
        mock_file.download_url = None

        mock_record = Mock(spec=Record)
        mock_record.get_child.return_value = mock_file

        mock_get_record.return_value = mock_record

        with self.assertRaises(DataNotFoundException) as context:
            self.source.download_file_by_id_and_filename(123456, "test.txt")

        self.assertIn("No download link found for file", str(context.exception))

    @patch.object(SourceZenodoRequest, "get_record")
    @patch("requests.get")
    def test_download_file_by_id_and_filename_http_error(
        self, mock_get, mock_get_record
    ):
        """Test of download_file_by_id_and_filename with HTTP error during download."""
        mock_file = Mock(spec=File)
        mock_file.name = "test_file.txt"
        mock_file.download_url = "http://example.com/download/test_file.txt"

        mock_record = Mock(spec=Record)
        mock_record.get_child.return_value = mock_file

        mock_get_record.return_value = mock_record

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error")
        mock_get.return_value = mock_response

        with self.assertRaises(DataAccessException) as context:
            self.source.download_file_by_id_and_filename(123456, "test_file.txt")

        self.assertIn("Failed to download file", str(context.exception))

    @patch.object(SourceZenodoRequest, "get_record")
    @patch("requests.get")
    def test_download_file_by_id_and_filename_custom_dest_path(
        self, mock_get, mock_get_record
    ):
        """Test of download_file_by_id_and_filename with custom destination path."""
        mock_file = Mock(spec=File)
        mock_file.name = "test_file.txt"
        mock_file.download_url = "http://example.com/download/test_file.txt"

        mock_record = Mock(spec=Record)
        mock_record.get_child.return_value = mock_file

        mock_get_record.return_value = mock_record

        mock_response = Mock()
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = os.path.join(temp_dir, "custom_name.txt")
            result_path = self.source.download_file_by_id_and_filename(
                123456, "test_file.txt", custom_path
            )

            self.assertEqual(result_path, custom_path)
            self.assertTrue(os.path.exists(custom_path))

    @patch.object(SourceZenodoRequest, "get_record")
    @patch("requests.get")
    def test_download_file_by_id_and_filename_no_name(self, mock_get, mock_get_record):
        """Test of download_file_by_id_and_filename with file without name."""
        mock_file = Mock(spec=File)
        mock_file.name = None  # Without name
        mock_file.download_url = "http://example.com/download/test_file.txt"

        mock_record = Mock(spec=Record)
        mock_record.id = 123456
        mock_record.get_child.return_value = mock_file

        mock_get_record.return_value = mock_record

        mock_response = Mock()
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = self.source.download_file_by_id_and_filename(
                123456, "test_file.txt", temp_dir
            )

            # Should use a default name
            self.assertIn("record_123456_file", result_path)
            self.assertTrue(os.path.exists(result_path))
