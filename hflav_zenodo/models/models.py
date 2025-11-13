from typing import List
from pydantic import BaseModel


class File(BaseModel):
    name: str
    download_url: str


class Record(BaseModel):
    id: int
    doi: str
    title: str
    created: str
    updated: str
    links: dict
    files: List[File]


class Template(BaseModel):
    title: str
    created: str
    updated: str
    version: str
    jsons: List[dict]
