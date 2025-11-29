import datetime
from hflav_zenodo.container import Container
from hflav_zenodo.filters.search_filters import AndFilter, OrFilter, QueryBuilder
from hflav_zenodo.filters.zenodo_query import ZenodoQuery

container = Container()

service = container.service()

query = (
    QueryBuilder(query=ZenodoQuery)
    .with_text(field="title", value="HFLAV")
    .with_pagination(size=5, page=1)
    .with_date_range(
        field="created",
        start_date=datetime.datetime(2025, 1, 1),
        end_date=datetime.datetime(2025, 12, 31),
    )
    .build(combinator=OrFilter)
)

dynamic_class = service.search_and_load_data_file(query=query)
# services.search_records_by_name(query="HFLAV", size=5, page=1)
# dynamic_class = services.load_data_file(
#     record_id=11157260, filename="sin2beta_example.json"
# )
# average = HFLAVApp()
# client = Zenodo()
# path = average.get_json(
#     client=client, record_id=13989054, name="hflav-tau-lifetime.json"
# )
# new_try = ZenodoClient()
# new_try.get_files_by_name(query="tau lifetime")
# new_try.get_file_by_id(id=13989054, filename="hflav-tau-mass.json")
# print("Downloaded file to:", path)
# inst = average.from_json(path)
# print("Instantiated average from JSON:", inst)
# inst2 = average.from_zenodo(
#     client=client, record_id=13989054, name="hflav-tau-br-uc.json"
# )
# print("Instantiated average from Zenodo:", inst2)
# json_str = average.to_json()
# print("Serialized average to JSON string:", json_str)
