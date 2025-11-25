from abc import abstractmethod, abstractproperty
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, model_validator


class ZenodoElement(BaseModel):
    """Base component for the Composite pattern.

    Kept lightweight for Pydantic compatibility (no ABC/abstractmethod).
    Subclasses should override get_data(); 'name' is provided via a field or property.
    """

    @abstractmethod
    def get_data(self) -> dict:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def is_leaf(self) -> bool:
        return not hasattr(self, "children")


class File(ZenodoElement):
    title: str
    download_url: str

    @property
    def name(self) -> str:
        return self.title

    @model_validator(mode="before")
    def transform_json_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                "title": data.get("key", ""),
                "download_url": data.get("links", {}).get("self", ""),
            }
        return data

    def get_data(self) -> dict:
        return {"name": self.name, "download_url": self.download_url}

    def __str__(self):
        return f"File(name='{self.name}', download_url='{self.download_url}')"


class Record(ZenodoElement):
    id: int
    doi: str
    title: str
    created: datetime
    updated: datetime
    links: dict
    children: List[ZenodoElement]

    @model_validator(mode="before")
    def transform_json_data(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(values, dict):
            files = [File(**file) for file in values.get("files", [])]
            transformed = {
                "id": values.get("id"),
                "doi": values.get("doi"),
                "title": values.get("metadata", {}).get("title"),
                "created": values.get("created"),
                "updated": values.get("updated"),
                "links": values.get("links", {}),
                "children": files,
            }
            return transformed
        return values

    @property
    def name(self) -> str:
        return self.title

    def add_child(self, child: ZenodoElement) -> None:
        if self.children is None:
            self.children = []
        self.children.append(child)

    def remove_child(self, child_name: str) -> None:
        if not self.children:
            return
        self.children = [c for c in self.children if c.name != child_name]

    def get_child(self, child_name: str) -> ZenodoElement:
        if not self.children:
            raise ValueError(f"No children in record {self.id}")
        for c in self.children:
            if c.name == child_name:
                return c
        raise ValueError(f"Child with name {child_name} not found in record {self.id}")

    def get_data(self) -> dict:
        return {
            "id": self.id,
            "doi": self.doi,
            "title": self.title,
            "created": self.created,
            "updated": self.updated,
            "links": self.links,
            "children": [c.get_data() for c in (self.children or [])],
        }

    def __str__(self):
        children_str = ",\n            ".join(
            f"{i+1}: {str(c)}" for i, c in enumerate(self.children or [])
        )
        return (
            "Record(\n"
            f"  id={self.id},\n"
            f"  title='{self.title}',\n"
            f"  doi='{self.doi}',\n"
            f"  created={self.created},\n"
            f"  updated={self.updated},\n"
            f"  children=[\n            {children_str}\n  ]\n)"
        )


class Template(ZenodoElement):
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

    @property
    def name(self) -> str:
        return self.title

    def get_data(self) -> dict:
        return {
            "rec_id": self.rec_id,
            "title": self.title,
            "created": self.created,
            "updated": self.updated,
            "version": self.version,
            "jsons": [c.get_data() for c in (self.jsons or [])],
        }
