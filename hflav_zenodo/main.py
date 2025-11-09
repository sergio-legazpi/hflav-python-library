from dotenv import load_dotenv
from zenodo_client import Zenodo

from hflav_zenodo.averages.averages import Average


load_dotenv()

average = Average()
client = Zenodo()
path = average.get_json(client=client, record_id=13989054, name="hflav-tau-br-uc.json")
print("Downloaded file to:", path)
inst = average.from_json(path)
print("Instantiated average from JSON:", inst)
inst2 = average.from_zenodo(
    client=client, record_id=13989054, name="hflav-tau-br-uc.json"
)
print("Instantiated average from Zenodo:", inst2)
json_str = average.to_json()
print("Serialized average to JSON string:", json_str)
