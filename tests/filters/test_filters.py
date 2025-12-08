import pytest
import datetime
from abc import abstractmethod
from typing import Type, Union
from unittest.mock import Mock, MagicMock, patch, create_autospec

from hflav_zenodo.filters.base_query import BaseQuery
from hflav_zenodo.filters.search_filters import (
    Filter,
    TextFilter,
    DateRangeFilter,
    NumericFilter,
    ExistenceFilter,
    AndFilter,
    OrFilter,
    NotFilter,
    SortOptions,
    QueryBuilder,
)
from hflav_zenodo.filters.zenodo_query import ZenodoQuery


class TestBaseQuery:
    """Tests for BaseQuery abstract class."""

    def test_base_query_is_abstract(self):
        """Test that BaseQuery cannot be instantiated directly."""
        try:
            # Mock filter since BaseQuery requires it
            mock_filter = Mock(spec=Filter)
            query = BaseQuery(filter=mock_filter, sort="mostrecent")

            assert hasattr(query, "build_params")
            assert hasattr(query, "build_query_string")

            with pytest.raises(NotImplementedError):
                query.build_params()

            with pytest.raises(NotImplementedError):
                query.build_query_string()

        except TypeError as e:
            assert "abstract" in str(e).lower() or "instantiate" in str(e).lower()

    def test_base_query_has_required_methods(self):
        """Test that BaseQuery defines required abstract methods."""
        assert hasattr(BaseQuery, "build_params")
        assert hasattr(BaseQuery, "build_query_string")

        class ConcreteQuery(BaseQuery):
            def build_params(self) -> dict:
                return {"test": "value"}

            def build_query_string(self) -> str:
                return "test query"

        mock_filter = Mock(spec=Filter)
        query = ConcreteQuery(filter=mock_filter, sort="mostrecent", size=10, page=1)
        assert isinstance(query, BaseQuery)
        assert query.build_params() == {"test": "value"}
        assert query.build_query_string() == "test query"


class TestFilterClasses:
    """Tests for Filter interface and concrete implementations."""

    def test_filter_is_abstract(self):
        """Test that Filter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            filter = Filter()

    def test_text_filter_build_query(self):
        """Test TextFilter builds correct query string."""
        filter = TextFilter(field="title", value="test")
        query = filter.build_query()
        assert query == 'title:"test"'

    def test_text_filter_with_custom_operator(self):
        """Test TextFilter with custom operator."""
        filter = TextFilter(
            field="metadata.description", value="experiment", operator="="
        )
        query = filter.build_query()
        assert query == 'metadata.description="experiment"'

    def test_date_range_filter_build_query(self):
        """Test DateRangeFilter builds correct query string."""
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        filter = DateRangeFilter(
            field="created", start_date=start_date, end_date=end_date
        )

        query = filter.build_query()
        expected_start = "2023-01-01T00:00:00"
        expected_end = "2023-12-31T00:00:00"
        assert query == f"created:[{expected_start} TO {expected_end}]"

    def test_numeric_filter_build_query(self):
        """Test NumericFilter builds correct query string."""
        filter = NumericFilter(field="version", value=2)
        query = filter.build_query()
        assert query == "version:2"

    def test_numeric_filter_with_operator(self):
        """Test NumericFilter with comparison operators."""
        filter = NumericFilter(field="version", value=2, operator=">=")
        query = filter.build_query()
        assert query == "version>=2"

    def test_existence_filter_build_query_exists(self):
        """Test ExistenceFilter for field existence."""
        filter = ExistenceFilter(field="metadata.keywords", exists=True)
        query = filter.build_query()
        assert query == "_exists_:metadata.keywords"

    def test_existence_filter_build_query_not_exists(self):
        """Test ExistenceFilter for field non-existence."""
        filter = ExistenceFilter(field="metadata.keywords", exists=False)
        query = filter.build_query()
        assert query == "NOT _exists_:metadata.keywords"

    def test_and_filter_build_query(self):
        """Test AndFilter combines multiple filters."""
        filter1 = TextFilter(field="title", value="test")
        filter2 = NumericFilter(field="version", value=1)

        and_filter = AndFilter(filter1, filter2)
        query = and_filter.build_query()

        assert query == '(title:"test") AND (version:1)'

    def test_and_filter_empty(self):
        """Test AndFilter with no filters."""
        and_filter = AndFilter()
        query = and_filter.build_query()
        assert query == ""

    def test_or_filter_build_query(self):
        """Test OrFilter combines multiple filters."""
        filter1 = TextFilter(field="title", value="test1")
        filter2 = TextFilter(field="title", value="test2")

        or_filter = OrFilter(filter1, filter2)
        query = or_filter.build_query()

        assert query == '(title:"test1") OR (title:"test2")'

    def test_not_filter_build_query(self):
        """Test NotFilter negates filters."""
        filter1 = TextFilter(field="title", value="test")

        not_filter = NotFilter(filter1)
        query = not_filter.build_query()

        assert query == 'NOT (title:"test")'

    def test_not_filter_multiple_filters(self):
        """Test NotFilter with multiple filters."""
        filter1 = TextFilter(field="title", value="test1")
        filter2 = TextFilter(field="title", value="test2")

        not_filter = NotFilter(filter1, filter2)
        query = not_filter.build_query()

        assert query == 'NOT (title:"test1") AND NOT (title:"test2")'

    def test_complex_nested_filter(self):
        """Test complex nested filter structure."""
        # Create a complex query: (title:"test" AND version:2) OR NOT (created:[...])
        text_filter = TextFilter(field="title", value="test")
        numeric_filter = NumericFilter(field="version", value=2)
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        date_filter = DateRangeFilter(
            field="created", start_date=start_date, end_date=end_date
        )

        and_filter = AndFilter(text_filter, numeric_filter)
        not_filter = NotFilter(date_filter)
        or_filter = OrFilter(and_filter, not_filter)

        query = or_filter.build_query()
        expected_date = "created:[2023-01-01T00:00:00 TO 2023-12-31T00:00:00]"
        assert query == f'((title:"test") AND (version:2)) OR (NOT ({expected_date}))'


class TestSortOptions:
    """Tests for SortOptions enum."""

    def test_sort_options_values(self):
        """Test SortOptions enum values."""
        assert SortOptions.MOSTRECENT.value == "mostrecent"
        assert SortOptions.BESTMATCH.value == "bestmatch"

    def test_sort_options_enum_membership(self):
        """Test SortOptions enum membership."""
        assert isinstance(SortOptions.MOSTRECENT, SortOptions)
        assert isinstance(SortOptions.BESTMATCH, SortOptions)


class TestQueryBuilder:
    """Tests for QueryBuilder class."""

    def test_query_builder_initialization_without_injection(self):
        """Test QueryBuilder initializes with default values without DI."""
        # Patch the inject decorator to bypass dependency injection
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            # Create QueryBuilder directly
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)

            assert builder.filters == []
            assert builder.sort == "mostrecent"
            assert builder.page_size == 10
            assert builder.page == 1
            assert builder.query is None

    def test_query_builder_with_text(self):
        """Test adding text filter to QueryBuilder."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)

            result = builder.with_text(field="title", value="experiment")

            assert len(builder.filters) == 1
            assert isinstance(builder.filters[0], TextFilter)
            assert builder.filters[0].field == "title"
            assert builder.filters[0].value == "experiment"
            assert result is builder  # Returns self

    def test_query_builder_with_date_range(self):
        """Test adding date range filter to QueryBuilder."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)

            start_date = datetime.datetime(2023, 1, 1)
            end_date = datetime.datetime(2023, 12, 31)

            result = builder.with_date_range(
                field="created", start_date=start_date, end_date=end_date
            )

            assert len(builder.filters) == 1
            assert isinstance(builder.filters[0], DateRangeFilter)
            assert builder.filters[0].field == "created"
            assert builder.filters[0].start_date == start_date
            assert builder.filters[0].end_date == end_date
            assert result is builder

    def test_query_builder_with_number(self):
        """Test adding numeric filter to QueryBuilder."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)

            result = builder.with_number(field="version", value=2, operator=">=")

            assert len(builder.filters) == 1
            assert isinstance(builder.filters[0], NumericFilter)
            assert builder.filters[0].field == "version"
            assert builder.filters[0].value == 2
            assert builder.filters[0].operator == ">="
            assert result is builder

    def test_query_builder_with_existence(self):
        """Test adding existence filter to QueryBuilder."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)

            result = builder.with_existence(field="metadata.keywords", exists=True)

            assert len(builder.filters) == 1
            assert isinstance(builder.filters[0], ExistenceFilter)
            assert builder.filters[0].field == "metadata.keywords"
            assert builder.filters[0].exists == True
            assert result is builder

    def test_query_builder_order_by(self):
        """Test setting sort order in QueryBuilder."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)

            result = builder.order_by(field=SortOptions.MOSTRECENT)
            assert builder.sort == "mostrecent"
            assert result is builder

            result = builder.order_by(field=SortOptions.MOSTRECENT, desc=True)
            assert builder.sort == "-mostrecent"
            assert result is builder

            result = builder.order_by(field=SortOptions.BESTMATCH)
            assert builder.sort == "bestmatch"
            assert result is builder

    def test_query_builder_with_pagination(self):
        """Test setting pagination in QueryBuilder."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)

            result = builder.with_pagination(size=25, page=3)

            assert builder.page_size == 25
            assert builder.page == 3
            assert result is builder

    def test_query_builder_merge_filters(self):
        """Test merging filters from another QueryBuilder."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            # Create first builder with filters
            builder1 = QueryBuilder.__new__(QueryBuilder)
            builder1.__init__(query=None)
            builder1.with_text(field="title", value="test1")
            builder1.with_number(field="version", value=1)

            # Create second builder with different filters
            builder2 = QueryBuilder.__new__(QueryBuilder)
            builder2.__init__(query=None)
            builder2.with_text(field="author", value="john")

            # Merge filters
            builder1.merge_filters(builder2)

            assert len(builder1.filters) == 3
            assert builder1.filters[0].field == "title"
            assert builder1.filters[1].field == "version"
            assert builder1.filters[2].field == "author"

    def test_query_builder_apply_combinator_and(self):
        """Test applying AND combinator to filters."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)
            builder.with_text(field="title", value="test1")
            builder.with_text(field="title", value="test2")

            result = builder.apply_combinator(AndFilter)

            assert len(builder.filters) == 1
            assert isinstance(builder.filters[0], AndFilter)
            assert len(builder.filters[0].filters) == 2
            assert result is builder

    def test_query_builder_apply_combinator_or(self):
        """Test applying OR combinator to filters."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)
            builder.with_text(field="title", value="test1")
            builder.with_number(field="version", value=2)

            result = builder.apply_combinator(OrFilter)

            assert len(builder.filters) == 1
            assert isinstance(builder.filters[0], OrFilter)
            assert len(builder.filters[0].filters) == 2
            assert result is builder

    def test_query_builder_apply_combinator_not(self):
        """Test applying NOT combinator to filters."""
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=None)
            builder.with_text(field="title", value="test")

            result = builder.apply_combinator(NotFilter)

            assert len(builder.filters) == 1
            assert isinstance(builder.filters[0], NotFilter)
            assert len(builder.filters[0].filters) == 1
            assert result is builder

    def test_query_builder_build_with_default_operator(self):
        """Test building query with default AND operator."""
        # Mock the query parameter
        mock_query_class = Mock()
        mock_query_instance = Mock()
        mock_query_class.return_value = mock_query_instance

        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=mock_query_class)
            builder.with_text(field="title", value="test1")
            builder.with_text(field="author", value="john")
            builder.order_by(field=SortOptions.MOSTRECENT)
            builder.with_pagination(size=20, page=2)

            result = builder.build()

            # Should call the query constructor with the right arguments
            mock_query_class.assert_called_once()
            call_args = mock_query_class.call_args

            # Check filter argument
            filter_arg = call_args[0][0]
            assert isinstance(filter_arg, AndFilter)
            assert len(filter_arg.filters) == 2

            # Check other arguments
            assert call_args[0][1] == "mostrecent"  # sort
            assert call_args[0][2] == 20  # size
            assert call_args[0][3] == 2  # page

            assert result == mock_query_instance

    def test_query_builder_build_with_single_filter(self):
        """Test building query with single filter (no combinator)."""
        mock_query_class = Mock()
        mock_query_instance = Mock()
        mock_query_class.return_value = mock_query_instance

        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=mock_query_class)
            builder.with_text(field="title", value="test")

            result = builder.build()

            mock_query_class.assert_called_once()
            call_args = mock_query_class.call_args
            filter_arg = call_args[0][0]

            assert isinstance(filter_arg, TextFilter)
            assert filter_arg.field == "title"
            assert result == mock_query_instance

    def test_query_builder_build_with_no_filters(self):
        """Test building query with no filters."""
        mock_query_class = Mock()
        mock_query_instance = Mock()
        mock_query_class.return_value = mock_query_instance

        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=mock_query_class)

            result = builder.build()

            mock_query_class.assert_called_once()
            call_args = mock_query_class.call_args
            filter_arg = call_args[0][0]

            assert filter_arg is None
            assert result == mock_query_instance

    def test_query_builder_build_with_custom_operator(self):
        """Test building query with custom default operator."""
        mock_query_class = Mock()
        mock_query_instance = Mock()
        mock_query_class.return_value = mock_query_instance

        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=mock_query_class)
            builder.with_text(field="title", value="test1")
            builder.with_text(field="title", value="test2")

            result = builder.build(default_operator=OrFilter)

            mock_query_class.assert_called_once()
            call_args = mock_query_class.call_args
            filter_arg = call_args[0][0]

            assert isinstance(filter_arg, OrFilter)
            assert len(filter_arg.filters) == 2
            assert result == mock_query_instance

    def test_query_builder_fluent_interface(self):
        """Test fluent interface of QueryBuilder."""
        mock_query_class = Mock()
        mock_query_instance = Mock()
        mock_query_class.return_value = mock_query_instance

        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=mock_query_class)

            start_date = datetime.datetime(2023, 1, 1)
            end_date = datetime.datetime(2023, 12, 31)

            result = (
                builder.with_text(field="title", value="experiment")
                .with_date_range(
                    field="created", start_date=start_date, end_date=end_date
                )
                .with_number(field="version", value=2, operator=">=")
                .order_by(field=SortOptions.MOSTRECENT, desc=True)
                .with_pagination(size=50, page=1)
                .apply_combinator(AndFilter)
            )

            # Verify all methods were called and returned self
            assert len(builder.filters) == 1  # Combined by AndFilter
            assert isinstance(builder.filters[0], AndFilter)
            assert builder.sort == "-mostrecent"
            assert builder.page_size == 50
            assert builder.page == 1
            assert result is builder


class TestZenodoQuery:
    """Tests for ZenodoQuery class."""

    def test_zenodo_query_implements_base_query(self):
        """Test that ZenodoQuery implements BaseQuery interface."""
        mock_filter = Mock(spec=Filter)
        query = ZenodoQuery(filter=mock_filter, sort="mostrecent")
        assert isinstance(query, BaseQuery)

    def test_zenodo_query_default_community(self):
        """Test ZenodoQuery has default community constant."""
        assert hasattr(ZenodoQuery, "DEFAULT_COMMUNITY")
        assert ZenodoQuery.DEFAULT_COMMUNITY == "hflav"

    def test_zenodo_query_build_query_string_with_filter(self):
        """Test building query string with filter."""
        mock_filter = Mock(spec=Filter)
        mock_filter.build_query.return_value = 'title:"test"'

        query = ZenodoQuery(filter=mock_filter, sort="mostrecent")
        query_string = query.build_query_string()

        assert query_string == 'title:"test"'
        mock_filter.build_query.assert_called_once()

    def test_zenodo_query_build_query_string_without_filter(self):
        """Test building query string without filter."""
        query = ZenodoQuery(filter=None, sort="mostrecent")
        query_string = query.build_query_string()

        assert query_string == ""

    def test_zenodo_query_build_params_with_filter(self):
        """Test building params with filter."""
        mock_filter = Mock(spec=Filter)
        mock_filter.build_query.return_value = 'title:"test"'

        query = ZenodoQuery(filter=mock_filter, sort="-mostrecent", size=25, page=3)

        params = query.build_params()

        assert params == {
            "communities": "hflav",
            "size": 25,
            "page": 3,
            "q": 'title:"test"',
            "sort": "-mostrecent",
        }

    def test_zenodo_query_build_params_without_filter(self):
        """Test building params without filter."""
        query = ZenodoQuery(filter=None, sort="bestmatch", size=10, page=1)

        params = query.build_params()

        assert params == {
            "communities": "hflav",
            "size": 10,
            "page": 1,
            "sort": "bestmatch",
        }
        # 'q' should not be in params when no filter
        assert "q" not in params

    def test_zenodo_query_str_representation(self):
        """Test string representation of ZenodoQuery."""
        mock_filter = Mock(spec=Filter)
        mock_filter.build_query.return_value = 'title:"experiment" AND version:2'

        query = ZenodoQuery(filter=mock_filter, sort="mostrecent")
        str_repr = str(query)

        assert str_repr == 'title:"experiment" AND version:2'

    def test_zenodo_query_with_complex_filter(self):
        """Test ZenodoQuery with complex filter structure."""
        # Create a complex filter tree
        text_filter = TextFilter(field="title", value="test")
        numeric_filter = NumericFilter(field="version", value=2)
        and_filter = AndFilter(text_filter, numeric_filter)

        query = ZenodoQuery(filter=and_filter, sort="mostrecent", size=15, page=2)
        query_string = query.build_query_string()

        assert query_string == '(title:"test") AND (version:2)'

        params = query.build_params()
        assert params["q"] == '(title:"test") AND (version:2)'
        assert params["size"] == 15
        assert params["page"] == 2

    def test_zenodo_query_initialization_defaults(self):
        """Test ZenodoQuery initialization with default parameters."""
        query = ZenodoQuery(filter=None, sort="mostrecent")

        assert query.filter is None
        assert query.sort == "mostrecent"
        assert query.size == 10  # Default from BaseQuery
        assert query.page == 1  # Default from BaseQuery

    def test_zenodo_query_custom_parameters(self):
        """Test ZenodoQuery initialization with custom parameters."""
        mock_filter = Mock(spec=Filter)
        query = ZenodoQuery(filter=mock_filter, sort="bestmatch", size=100, page=5)

        assert query.filter == mock_filter
        assert query.sort == "bestmatch"
        assert query.size == 100
        assert query.page == 5


class TestIntegration:
    """Integration tests for the full query building workflow."""

    def test_complete_query_building_workflow(self):
        """Test complete workflow from QueryBuilder to ZenodoQuery."""
        # Create filters
        text_filter = TextFilter(field="title", value="experiment")
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        date_filter = DateRangeFilter(
            field="created", start_date=start_date, end_date=end_date
        )

        # Combine with AND
        and_filter = AndFilter(text_filter, date_filter)

        # Create ZenodoQuery
        query = ZenodoQuery(filter=and_filter, sort="-mostrecent", size=20, page=1)

        # Test query string
        query_string = query.build_query_string()
        expected_date = "created:[2023-01-01T00:00:00 TO 2023-12-31T00:00:00]"
        assert query_string == f'(title:"experiment") AND ({expected_date})'

        # Test params
        params = query.build_params()
        assert params["q"] == query_string
        assert params["sort"] == "-mostrecent"
        assert params["size"] == 20
        assert params["page"] == 1
        assert params["communities"] == "hflav"

    def test_fluent_builder_to_query(self):
        """Test fluent builder pattern ending with ZenodoQuery."""
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)

        # Mock the inject decorator
        with patch("hflav_zenodo.filters.search_filters.inject", lambda x: x):
            # Create QueryBuilder with ZenodoQuery as the query class
            builder = QueryBuilder.__new__(QueryBuilder)
            builder.__init__(query=ZenodoQuery)

            # Build query using fluent interface
            query = (
                builder.with_text(field="title", value="test")
                .with_date_range(
                    field="created", start_date=start_date, end_date=end_date
                )
                .order_by(field=SortOptions.MOSTRECENT, desc=True)
                .with_pagination(size=30, page=2)
                .apply_combinator(AndFilter)
                .build()
            )

            # Verify the result is a ZenodoQuery
            assert isinstance(query, ZenodoQuery)
            assert query.sort == "-mostrecent"
            assert query.size == 30
            assert query.page == 2
            assert query.filter is not None
            assert isinstance(query.filter, AndFilter)
