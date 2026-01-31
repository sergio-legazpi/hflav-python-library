import datetime
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from dotenv import load_dotenv
import pytest

from hflav_fair_client.container import Container
from hflav_fair_client.filters.search_filters import (
    AndFilter,
    NotFilter,
    OrFilter,
    QueryBuilder,
    SortOptions,
)
from hflav_fair_client.filters.zenodo_query import ZenodoQuery
from hflav_fair_client.models.hflav_data_searching import HflavDataSearching, SearchOperators

load_dotenv()

# Create container and service ONCE per class, not at module level
container = Container()
container.init_resources()
service = container.service()


class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test data before each test"""
        # Create specific queries for each test
        self.query1 = (
            QueryBuilder()
            .with_number(field="version", value=2, operator=">=")
            .apply_combinator(NotFilter)
        )
        self.query2 = (
            QueryBuilder()
            .with_text(field="title", value="HFLAV")
            .with_date_range(
                field="created",
                start_date=datetime.datetime(2022, 1, 1),
                end_date=datetime.datetime(2025, 12, 31),
            )
            .apply_combinator(OrFilter)
        )
        self.query = (
            QueryBuilder()
            .with_pagination(size=5, page=1)
            .order_by(field=SortOptions.MOSTRECENT)
            .merge_filters(self.query1)
            .merge_filters(self.query2)
            .build()
        )

    @pytest.mark.integration
    @patch("builtins.input", side_effect=[1, 1])
    def test_integration_search_and_load_data_file(self, mock_input):
        """Integration test for search and data file loading"""
        # Test 1: First call
        dynamic_class = service.search_and_load_data_file(query=self.query)
        self.assertIsNotNone(dynamic_class, "First call should not return None")

        # Verify that mocked inputs were used
        self.assertEqual(mock_input.call_count, 2)
        mock_input.assert_any_call()  # Verify that input was called

        self.assertIsInstance(
            dynamic_class, SimpleNamespace, "Returned data should be a SimpleNamespace"
        )

    @pytest.mark.integration
    def test_service_initialization(self):
        """Test to verify service initializes correctly"""
        self.assertIsNotNone(service, "Service should not be None")
        # Here you can add more service verifications

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        # If container has cleanup method
        if hasattr(container, "shutdown_resources"):
            container.shutdown_resources()


if __name__ == "__main__":
    unittest.main()
