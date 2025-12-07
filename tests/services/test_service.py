import pytest
from unittest.mock import Mock, patch, MagicMock, call
from types import SimpleNamespace
from typing import List, Optional

from hflav_zenodo.filters.base_query import BaseQuery
from hflav_zenodo.models.models import Record
from hflav_zenodo.exceptions.source_exceptions import DataAccessException
from hflav_zenodo.services.service import Service
from hflav_zenodo.services.service_interface import ServiceInterface


class TestService:
    """Test suite for Service class focusing on public interface."""

    @pytest.fixture
    def mock_source(self):
        """Mock for SourceInterface dependency."""
        return Mock()

    @pytest.fixture
    def mock_conversor(self):
        """Mock for ConversorInterface dependency."""
        return Mock()

    @pytest.fixture
    def mock_command_invoker(self):
        """Mock for CommandInvoker dependency."""
        return Mock()

    @pytest.fixture
    def mock_handler_schema_chain(self):
        """Mock for handler_schema_chain dependency."""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_source,
        mock_conversor,
        mock_command_invoker,
        mock_handler_schema_chain,
    ):
        """Create Service instance with mocked dependencies."""
        return Service(
            source=mock_source,
            conversor=mock_conversor,
            command_invoker=mock_command_invoker,
            handler_schema_chain=mock_handler_schema_chain,
        )

    @pytest.fixture
    def mock_query(self):
        """Mock BaseQuery object."""
        query = Mock(spec=BaseQuery)
        query.__str__ = Mock(return_value="test query")
        return query

    @pytest.fixture
    def mock_record(self):
        """Mock Record object."""
        record = Mock(spec=Record)
        record.id = 123
        record.title = "Test Record"
        record.created = "2024-01-01"
        record.__str__ = Mock(return_value="Record 123: Test Record")
        return record

    @pytest.fixture
    def mock_template(self):
        """Mock template object."""
        template = Mock()
        template.title = "Test Template"
        template.version = "v1.0"
        return template

    @pytest.fixture
    def mock_data_object(self):
        """Mock data object as SimpleNamespace."""
        data = SimpleNamespace()
        data.name = "test"
        data.value = 123
        return data

    # Test search_records_by_name method
    def test_search_records_by_name_success(
        self, service, mock_source, mock_query, mock_record
    ):
        """Test successful search of records by name."""
        # Setup
        expected_records = [mock_record, mock_record]
        mock_source.get_records_by_name.return_value = expected_records

        # Execute
        result = service.search_records_by_name(mock_query)

        # Verify
        mock_source.get_records_by_name.assert_called_once_with(query=mock_query)
        assert result == expected_records
        assert len(result) == 2

    def test_search_records_by_name_empty_result(
        self, service, mock_source, mock_query
    ):
        """Test search when no records are found."""
        # Setup
        mock_source.get_records_by_name.return_value = []

        # Execute
        result = service.search_records_by_name(mock_query)

        # Verify
        mock_source.get_records_by_name.assert_called_once_with(query=mock_query)
        assert result == []
        assert len(result) == 0

    def test_search_records_by_name_data_access_exception(
        self, service, mock_source, mock_query
    ):
        """Test search when DataAccessException is raised."""
        # Setup
        mock_source.get_records_by_name.side_effect = DataAccessException(
            "Connection failed"
        )

        # Execute
        result = service.search_records_by_name(mock_query)

        # Verify
        mock_source.get_records_by_name.assert_called_once_with(query=mock_query)
        assert result == []
        assert len(result) == 0

    def test_search_records_by_name_generic_exception(
        self, service, mock_source, mock_query
    ):
        """Test search when generic exception is raised."""
        # Setup
        mock_source.get_records_by_name.side_effect = Exception("Unexpected error")

        # Execute & Verify - debería propagar la excepción, no devolver lista vacía
        with pytest.raises(Exception) as exc_info:
            service.search_records_by_name(mock_query)

        assert "Unexpected error" in str(exc_info.value)
        mock_source.get_records_by_name.assert_called_once_with(query=mock_query)

    # Test search_and_load_data_file method
    def test_search_and_load_data_file_success(
        self, service, mock_command_invoker, mock_query, mock_data_object
    ):
        """Test successful search and load data file using command pattern."""
        # Setup
        mock_command_invoker.execute_command.return_value = mock_data_object

        # Execute
        result = service.search_and_load_data_file(mock_query)

        # Verify
        # Should create and set SearchAndLoadDataFile command
        mock_command_invoker.set_command.assert_called_once()
        command_arg = mock_command_invoker.set_command.call_args[0][0]
        assert command_arg._service == service
        assert command_arg._query == mock_query

        # Should execute the command
        mock_command_invoker.execute_command.assert_called_once()

        # Should return the data object
        assert result == mock_data_object

    def test_search_and_load_data_file_command_failure(
        self, service, mock_command_invoker, mock_query
    ):
        """Test search and load when command execution fails."""
        # Setup
        mock_command_invoker.execute_command.side_effect = ValueError("Command failed")

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            service.search_and_load_data_file(mock_query)

        assert "Command failed" in str(exc_info.value)
        mock_command_invoker.set_command.assert_called_once()
        mock_command_invoker.execute_command.assert_called_once()

    # Test load_data_file method
    def test_load_data_file_success(
        self,
        service,
        mock_source,
        mock_handler_schema_chain,
        mock_record,
        mock_template,
        mock_data_object,
    ):
        """Test successful loading of data file from record."""
        # Setup
        record_id = 123
        filename = "data.json"
        dest_path = "/tmp/download"
        downloaded_path = "/tmp/download/data.json"

        mock_source.get_record.return_value = mock_record
        mock_source.get_correct_template_by_date.return_value = mock_template
        mock_source.download_file_by_id_and_filename.return_value = downloaded_path
        mock_handler_schema_chain.handle.return_value = mock_data_object

        # Execute
        result = service.load_data_file(record_id, filename, dest_path)

        # Verify calls in correct order
        calls = [
            call.get_record(recid=record_id),
            call.get_correct_template_by_date(date=mock_record.created),
            call.download_file_by_id_and_filename(
                id=record_id, filename=filename, dest_path=dest_path
            ),
        ]
        mock_source.assert_has_calls(calls, any_order=False)

        mock_handler_schema_chain.handle.assert_called_once_with(
            mock_template, downloaded_path
        )

        assert result == mock_data_object

    def test_load_data_file_without_dest_path(
        self,
        service,
        mock_source,
        mock_handler_schema_chain,
        mock_record,
        mock_template,
        mock_data_object,
    ):
        """Test loading data file without destination path."""
        # Setup
        record_id = 123
        filename = "data.json"
        downloaded_path = "/some/default/path/data.json"

        mock_source.get_record.return_value = mock_record
        mock_source.get_correct_template_by_date.return_value = mock_template
        mock_source.download_file_by_id_and_filename.return_value = downloaded_path
        mock_handler_schema_chain.handle.return_value = mock_data_object

        # Execute
        result = service.load_data_file(record_id, filename)

        # Verify
        mock_source.download_file_by_id_and_filename.assert_called_once_with(
            id=record_id, filename=filename, dest_path=None
        )
        mock_handler_schema_chain.handle.assert_called_once_with(
            mock_template, downloaded_path
        )
        assert result == mock_data_object

    def test_load_data_file_record_not_found(self, service, mock_source):
        """Test loading when record is not found."""
        # Setup
        record_id = 999
        filename = "data.json"

        mock_source.get_record.side_effect = DataAccessException("Record not found")

        # Execute & Verify
        with pytest.raises(DataAccessException) as exc_info:
            service.load_data_file(record_id, filename)

        assert "Record not found" in str(exc_info.value)
        mock_source.get_record.assert_called_once_with(recid=record_id)
        mock_source.get_correct_template_by_date.assert_not_called()
        mock_source.download_file_by_id_and_filename.assert_not_called()

    def test_load_data_file_template_not_found(self, service, mock_source, mock_record):
        """Test loading when template is not found."""
        # Setup
        record_id = 123
        filename = "data.json"

        mock_source.get_record.return_value = mock_record
        mock_source.get_correct_template_by_date.side_effect = DataAccessException(
            "Template not found"
        )

        # Execute & Verify
        with pytest.raises(DataAccessException) as exc_info:
            service.load_data_file(record_id, filename)

        assert "Template not found" in str(exc_info.value)
        mock_source.get_record.assert_called_once_with(recid=record_id)
        mock_source.get_correct_template_by_date.assert_called_once_with(
            date=mock_record.created
        )
        mock_source.download_file_by_id_and_filename.assert_not_called()

    def test_load_data_file_download_fails(
        self,
        service,
        mock_source,
        mock_record,
        mock_template,
        mock_handler_schema_chain,
    ):
        """Test loading when file download fails."""
        # Setup
        record_id = 123
        filename = "data.json"

        mock_source.get_record.return_value = mock_record
        mock_source.get_correct_template_by_date.return_value = mock_template
        mock_source.download_file_by_id_and_filename.side_effect = DataAccessException(
            "Download failed"
        )

        # Execute & Verify
        with pytest.raises(DataAccessException) as exc_info:
            service.load_data_file(record_id, filename)

        assert "Download failed" in str(exc_info.value)
        mock_source.get_record.assert_called_once_with(recid=record_id)
        mock_source.get_correct_template_by_date.assert_called_once_with(
            date=mock_record.created
        )
        mock_source.download_file_by_id_and_filename.assert_called_once()
        mock_handler_schema_chain.handle.assert_not_called()

    # Test load_local_data_file_from_path method
    def test_load_local_data_file_from_path_with_schema_and_validation(
        self, service, mock_conversor, mock_data_object
    ):
        """Test loading local file with schema and validation."""
        # Setup
        file_path = "/path/to/data.json"
        schema_path = "/path/to/schema.json"

        mock_conversor.generate_instance_from_local_path.return_value = mock_data_object

        # Execute
        result = service.load_local_data_file_from_path(
            file_path=file_path, schema_path=schema_path, validate=True
        )

        # Verify
        mock_conversor.generate_instance_from_local_path.assert_called_once_with(
            data_path=file_path, schema_path=schema_path, validate=True
        )
        assert result == mock_data_object

    def test_load_local_data_file_from_path_without_schema(
        self, service, mock_conversor, mock_data_object
    ):
        """Test loading local file without schema."""
        # Setup
        file_path = "/path/to/data.json"

        mock_conversor.generate_instance_from_local_path.return_value = mock_data_object

        # Execute
        result = service.load_local_data_file_from_path(
            file_path=file_path, schema_path=None, validate=True
        )

        # Verify
        mock_conversor.generate_instance_from_local_path.assert_called_once_with(
            data_path=file_path, schema_path=None, validate=True
        )
        assert result == mock_data_object

    def test_load_local_data_file_from_path_without_validation(
        self, service, mock_conversor, mock_data_object
    ):
        """Test loading local file without validation."""
        # Setup
        file_path = "/path/to/data.json"

        mock_conversor.generate_instance_from_local_path.return_value = mock_data_object

        # Execute
        result = service.load_local_data_file_from_path(
            file_path=file_path, schema_path=None, validate=False
        )

        # Verify
        mock_conversor.generate_instance_from_local_path.assert_called_once_with(
            data_path=file_path, schema_path=None, validate=False
        )
        assert result == mock_data_object

    def test_load_local_data_file_from_path_conversor_fails(
        self, service, mock_conversor
    ):
        """Test loading local file when conversor fails."""
        # Setup
        file_path = "/path/to/data.json"

        mock_conversor.generate_instance_from_local_path.side_effect = ValueError(
            "Invalid JSON"
        )

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            service.load_local_data_file_from_path(file_path=file_path)

        assert "Invalid JSON" in str(exc_info.value)
        mock_conversor.generate_instance_from_local_path.assert_called_once_with(
            data_path=file_path, schema_path=None, validate=True
        )

    # Test ServiceInterface compliance
    def test_service_implements_interface(self):
        """Test that Service correctly implements ServiceInterface."""
        # This test verifies that Service can be instantiated
        # as a ServiceInterface (duck typing test)
        service = Service(
            source=Mock(),
            conversor=Mock(),
            command_invoker=Mock(),
            handler_schema_chain=Mock(),
        )

        assert isinstance(service, ServiceInterface)

        # Verify all abstract methods exist
        assert hasattr(service, "search_records_by_name")
        assert hasattr(service, "search_and_load_data_file")
        assert hasattr(service, "load_data_file")
        assert hasattr(service, "load_local_data_file_from_path")
        assert hasattr(service, "plot_data")

    # Test dependency injection
    def test_service_dependency_injection(
        self,
        mock_source,
        mock_conversor,
        mock_command_invoker,
        mock_handler_schema_chain,
    ):
        """Test that dependencies are properly injected."""
        service = Service(
            source=mock_source,
            conversor=mock_conversor,
            command_invoker=mock_command_invoker,
            handler_schema_chain=mock_handler_schema_chain,
        )

        assert service._source == mock_source
        assert service._conversor == mock_conversor
        assert service._command_invoker == mock_command_invoker
        assert service._handler_schema_chain == mock_handler_schema_chain

    # Test edge cases
    def test_search_records_by_name_with_special_characters(self, service, mock_source):
        """Test search with query containing special characters."""
        # Setup
        query = Mock(spec=BaseQuery)
        query.__str__ = Mock(return_value="test & query #123")

        expected_records = [Mock(spec=Record) for _ in range(2)]
        mock_source.get_records_by_name.return_value = expected_records

        # Execute
        result = service.search_records_by_name(query)

        # Verify
        mock_source.get_records_by_name.assert_called_once_with(query=query)
        assert result == expected_records

    def test_load_data_file_with_empty_filename(
        self, service, mock_source, mock_record, mock_template
    ):
        """Test loading with empty filename."""
        # Setup
        record_id = 123
        filename = ""
        downloaded_path = "/path/data.json"

        mock_source.get_record.return_value = mock_record
        mock_source.get_correct_template_by_date.return_value = mock_template
        mock_source.download_file_by_id_and_filename.return_value = downloaded_path
        mock_handler_schema_chain = Mock()
        service._handler_schema_chain = mock_handler_schema_chain
        mock_handler_schema_chain.handle.return_value = Mock()

        service.load_data_file(record_id, filename)

        mock_source.download_file_by_id_and_filename.assert_called_once_with(
            id=record_id, filename=filename, dest_path=None
        )

    def test_load_local_data_file_from_path_empty_path(self, service, mock_conversor):
        """Test loading with empty file path."""
        # Setup
        mock_conversor.generate_instance_from_local_path.side_effect = ValueError(
            "Data path must be provided"
        )

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            service.load_local_data_file_from_path(file_path="")

        assert "Data path must be provided" in str(exc_info.value)

    # Integration-style test
    def test_full_workflow_search_and_load(
        self, service, mock_source, mock_command_invoker, mock_query, mock_data_object
    ):
        """Test a complete workflow: search records then load one."""
        # Setup search
        mock_record1 = Mock(spec=Record)
        mock_record1.id = 1
        mock_record1.title = "Record 1"

        mock_record2 = Mock(spec=Record)
        mock_record2.id = 2
        mock_record2.title = "Record 2"

        mock_source.get_records_by_name.return_value = [mock_record1, mock_record2]

        # Execute search
        records = service.search_records_by_name(mock_query)
        assert len(records) == 2

        # Setup and execute load via command
        mock_command_invoker.execute_command.return_value = mock_data_object
        result = service.search_and_load_data_file(mock_query)

        assert result == mock_data_object
        mock_command_invoker.set_command.assert_called_once()
        mock_command_invoker.execute_command.assert_called_once()
