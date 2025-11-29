from abc import ABC, abstractmethod
import datetime
from enum import Enum
from typing import Any, Type, Union

from dependency_injector.wiring import inject, Provide

from hflav_zenodo.filters.base_query import BaseQuery


class Filter(ABC):
    """Basic interface for all filters. It follows the Interpreter design pattern."""

    @abstractmethod
    def build_query(self) -> str:
        """Build the query string for this filter."""
        pass


# Terminal filters
class TextFilter(Filter):
    def __init__(self, field: str, value: str, operator: str = ":"):
        self.field = field
        self.value = value
        self.operator = operator

    def build_query(self) -> str:
        return f'{self.field}{self.operator}"{self.value}"'


class DateRangeFilter(Filter):
    def __init__(self, field: str, start_date: datetime, end_date: datetime):
        self.field = field
        self.start_date = start_date
        self.end_date = end_date

    def build_query(self) -> str:
        start_str = self.start_date.isoformat()
        end_str = self.end_date.isoformat()
        return f"{self.field}:[{start_str} TO {end_str}]"


class NumericFilter(Filter):
    def __init__(self, field: str, value: Any, operator: str = ":"):
        self.field = field
        self.value = value
        self.operator = operator

    def build_query(self) -> str:
        return f"{self.field}{self.operator}{self.value}"


class ExistenceFilter(Filter):
    def __init__(self, field: str, exists: bool = True):
        self.field = field
        self.exists = exists

    def build_query(self) -> str:
        if self.exists:
            return f"_exists_:{self.field}"
        else:
            return f"NOT _exists_:{self.field}"


# Non-Terminal (Combinatorial) Filters
class AndFilter(Filter):
    def __init__(self, *filters: Filter):
        self.filters = filters

    def build_query(self) -> str:
        if not self.filters:
            return ""
        queries = [f"({filter.build_query()})" for filter in self.filters]
        return " AND ".join(queries)


class OrFilter(Filter):
    def __init__(self, *filters: Filter):
        self.filters = filters

    def build_query(self) -> str:
        if not self.filters:
            return ""
        queries = [f"({filter.build_query()})" for filter in self.filters]
        return " OR ".join(queries)


class NotFilter(Filter):
    def __init__(self, *filters: Filter):
        self.filters = filters

    def build_query(self) -> str:
        if not self.filters:
            return ""
        queries = [f"NOT ({filter.build_query()})" for filter in self.filters]
        return " AND ".join(queries)


class SortOptions(Enum):
    MOSTRECENT = "mostrecent"
    BESTMATCH = "bestmatch"


# Builder to create complex queries
class QueryBuilder:
    """
    Builder class for constructing complex queries with filters, sorting, and pagination.

    To check all the fields available for filtering and sorting, refer to the Zenodo API documentation:
    https://developers.zenodo.org/
    """

    @inject
    def __init__(self, query: BaseQuery = Provide["base_query"]):
        self.filters = []
        self.sort = SortOptions.MOSTRECENT.value
        self.page_size = 10
        self.page = 1
        self.query = query

    def with_text(self, field: str, value: str, operator: str = ":") -> "QueryBuilder":
        self.filters.append(TextFilter(field, value, operator))
        return self

    def with_date_range(
        self, field: str, start_date: datetime, end_date: datetime
    ) -> "QueryBuilder":
        self.filters.append(DateRangeFilter(field, start_date, end_date))
        return self

    def with_number(
        self, field: str, value: Any, operator: str = ":"
    ) -> "QueryBuilder":
        self.filters.append(NumericFilter(field, value, operator))
        return self

    def with_existence(self, field: str, exists: bool = True) -> "QueryBuilder":
        self.filters.append(ExistenceFilter(field, exists))
        return self

    def order_by(self, field: SortOptions, desc: bool = False) -> "QueryBuilder":
        direction = "-" if desc else ""
        self.sort = direction + field.value
        return self

    def with_pagination(self, size: int = 10, page: int = 1) -> "QueryBuilder":
        self.page_size = size
        self.page = page
        return self

    def merge_filters(self, query: "QueryBuilder") -> "QueryBuilder":
        filters = query.filters
        for filter in filters:
            self.filters.append(filter)
        return self

    def apply_combinator(
        self, combinator: Type[Union[AndFilter, OrFilter, NotFilter]]
    ) -> "QueryBuilder":
        if self.filters:
            combined_filter = combinator(*self.filters)
            self.filters = [combined_filter]
        return self

    def build(
        self, default_operator: Type[Union[AndFilter, OrFilter, NotFilter]] = AndFilter
    ) -> "BaseQuery":
        """
        Build the final query with optional default operator for combining filters.

        Args:
            default_operator: The operator to use when there is more than one filter.

        Returns:
            BaseQuery: The constructed query object ready for execution.

        Examples:
            >>> # Complex query with NOT combinator
            >>> query1 = (
            ...     QueryBuilder()
            ...     .with_number(field="version", value=2, operator=">=")
            ...     .apply_combinator(NotFilter)
            ... )
            >>>
            >>> # Query with OR combinator
            >>> query2 = (
            ...     QueryBuilder()
            ...     .with_text(field="title", value="HFLAV")
            ...     .with_date_range(
            ...         field="created",
            ...         start_date=datetime.datetime(2022, 1, 1),
            ...         end_date=datetime.datetime(2025, 12, 31),
            ...     )
            ...     .apply_combinator(OrFilter)
            ... )
            >>>
            >>> # Final combined query using default_operator
            >>> query = (
            ...     QueryBuilder()
            ...     .with_pagination(size=5, page=1)
            ...     .order_by(field=SortOptions.MOSTRECENT)
            ...     .merge_filters(query1)
            ...     .merge_filters(query2)
            ...     .build()  # Uses default_operator default value for final combination
            ... )
        """
        final_filter = (
            default_operator(*self.filters)
            if len(self.filters) > 1
            else self.filters[0] if self.filters else None
        )
        return self.query(final_filter, self.sort, self.page_size, self.page)
