from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, model_validator


class File(BaseModel):
    name: str
    download_url: str

    @model_validator(mode="before")
    def transform_json_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                "name": data.get("key", ""),
                "download_url": data.get("links", {}).get("self", ""),
            }
        return data


class Record(BaseModel):
    id: int
    doi: str
    title: str
    created: datetime
    updated: datetime
    links: dict
    files: List[File]

    @model_validator(mode="before")
    def transform_json_data(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(values, dict):
            transformed = {
                "id": values.get("id"),
                "doi": values.get("doi"),
                "title": values.get("metadata", {}).get("title"),
                "created": values.get("created"),
                "updated": values.get("updated"),
                "links": values.get("links", {}),
                "files": [File(**file) for file in values.get("files", [])],
            }
            return transformed
        return values

    def get_file_by_name(self, filename: str) -> File:
        for f in self.files:
            if f.name == filename:
                return f
        raise ValueError(f"File with name {filename} not found in record {self.id}")


class Template(BaseModel):
    rec_id: int
    title: str
    created: datetime
    updated: datetime
    version: str
    jsons: List[File]

    @model_validator(mode="before")
    def transform_json_data(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(values, dict):
            transformed = {
                "rec_id": values.get("id"),
                "title": values.get("metadata", {}).get("title"),
                "created": values.get("created"),
                "updated": values.get("updated"),
                "version": values.get("metadata", {}).get("version"),
                "jsons": [
                    File(**item)
                    for item in values.get("files", [])
                    if item["key"].endswith(".json")
                ],
            }
            return transformed
        return values
