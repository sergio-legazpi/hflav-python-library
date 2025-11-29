from abc import ABC, abstractmethod
import datetime
from typing import Any, Type, Union

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
    def __init__(self, filter: Filter):
        self.filter = filter

    def build_query(self) -> str:
        return f"NOT ({self.filter.build_query()})"


# Builder to create complex queries
class QueryBuilder:
    def __init__(self, query: BaseQuery):
        self.filters = []
        self.sorts = []
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

    def order_by(self, field: str, asc: bool = True) -> "QueryBuilder":
        direction = "asc" if asc else "desc"
        self.sorts.append(f"{field} {direction}")
        return self

    def with_pagination(self, size: int = 10, page: int = 1) -> "QueryBuilder":
        self.page_size = size
        self.page = page
        return self

    def build(
        self, combinator: Type[Union[AndFilter, OrFilter, NotFilter]]
    ) -> "BaseQuery":
        principal_filter = combinator(*self.filters) if self.filters else None
        return self.query(principal_filter, self.sorts, self.page_size, self.page)
