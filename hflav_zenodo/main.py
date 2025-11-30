import datetime
from hflav_zenodo.container import Container
from hflav_zenodo.filters.search_filters import (
    AndFilter,
    NotFilter,
    OrFilter,
    QueryBuilder,
    SortOptions,
)
from hflav_zenodo.filters.zenodo_query import ZenodoQuery

container = Container()

service = container.service()

query1 = (
    QueryBuilder()
    .with_number(field="version", value=2, operator=">=")
    .apply_combinator(NotFilter)
)
query2 = (
    QueryBuilder()
    .with_text(field="title", value="HFLAV")
    .with_date_range(
        field="created",
        start_date=datetime.datetime(2022, 1, 1),
        end_date=datetime.datetime(2025, 12, 31),
    )
    .apply_combinator(OrFilter)
)
query = (
    QueryBuilder()
    .with_pagination(size=5, page=1)
    .order_by(field=SortOptions.MOSTRECENT)
    .merge_filters(query1)
    .merge_filters(query2)
    .build()
)
dynamic_class = service.search_and_load_data_file(query=query)

# dynamic_class2 = service.load_local_data_file_from_path(
#    file_path="HFLAV.json", schema_path="HFLAV.schema", validate=False
# )
