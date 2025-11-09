from typing import Type, TypeVar, Union
from pathlib import Path
from pydantic import BaseModel, ConfigDict, ValidationError
from zenodo_client import Zenodo

from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, field_validator, Field
import dateutil.parser


class AverageValue(BaseModel):
    central: Optional[Union[List[float], float]] = None
    statistical: Optional[Union[List[float], float]] = None
    systematic: Optional[Union[List[float], float]] = None
    uncertainty: Optional[Union[List[float], float]] = None
    unit: Optional[str] = None
    upperlimit: Optional[float] = None


class AverageAverage(BaseModel):
    value: Optional[AverageValue] = None


class AverageElement(BaseModel):
    average: Optional[AverageAverage] = None
    comment: Optional[str] = None
    intervals: Optional[List[List[float]]] = None
    name: Optional[str] = None
    pd_gcode: Optional[str] = Field(default=None, alias="PDGcode")


class ContourX(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None


class Contour(BaseModel):
    cl: Optional[float] = Field(default=None, alias="CL")
    name: Optional[str] = None
    points: Optional[List[List[float]]] = None
    x: Optional[ContourX] = None
    y: Optional[ContourX] = None


class Fit(BaseModel):
    chi2: Optional[float] = None
    ndf: Optional[int] = None
    p: Optional[float] = None


class References(BaseModel):
    arxiv: Optional[str] = None
    bibtex: Optional[str] = None
    doi: Optional[str] = None
    pub: Optional[str] = None
    url: Optional[str] = None


class SourceValue(BaseModel):
    central: Optional[Union[List[float], float]] = None
    statistical: Optional[Union[List[float], float]] = None
    systematic: Optional[Union[List[float], float]] = None
    uncertainty: Optional[float] = None
    unit: Optional[str] = None


class Source(BaseModel):
    comment: Optional[str] = None
    name: Optional[str] = None
    references: Optional[References] = None
    value: Optional[SourceValue] = None


class Input(BaseModel):
    comment: Optional[str] = None
    intervals: Optional[List[List[float]]] = None
    name: Optional[str] = None
    sources: Optional[List[Source]] = None


class ScanX(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    values: Optional[List[float]] = None


class Scan(BaseModel):
    name: Optional[str] = None
    points: Optional[List[Union[List[float], float]]] = None
    x: Optional[ScanX] = None
    y: Optional[ScanX] = None


class Measurements(BaseModel):
    averages: Optional[List[AverageElement]] = None
    averages_correlation: Optional[List[List[float]]] = None
    contours: Optional[List[Contour]] = None
    fit: Optional[Fit] = None
    inputs: Optional[List[Input]] = None
    inputs_correlation: Optional[List[List[float]]] = None
    name: Optional[str] = None
    scans: Optional[List[Scan]] = None


class Metadata(BaseModel):
    author: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    schema_name: Optional[str] = Field(default=None, alias="schema")
    title: Optional[str] = None
    version: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return dateutil.parser.parse(value)
        except (ValueError, dateutil.parser.ParserError, OverflowError):
            return None


class Average(BaseModel):
    measurements: Optional[List[Measurements]] = None
    metadata: Optional[Metadata] = None

    @classmethod
    def get_json(cls, client: Zenodo, record_id: int, name: str) -> str:
        """Download JSON file from Zenodo using the client and return the local path."""
        return client.download(record_id=record_id, name=name)

    @classmethod
    def from_json(self, json_path_or_str: str) -> BaseModel:
        """Instantiate an average from a JSON file path (is_path=True) or a raw JSON string.

        Example:
            inst = MyAverage.from_json("/tmp/avg.json", client=my_client)
            inst = MyAverage.from_json(json_string, is_path=False)
        """
        try:
            inst = self.model_validate_json(Path(json_path_or_str).read_text())
        except ValidationError:
            raise
        return inst

    @classmethod
    def from_zenodo(self, client: Zenodo, record_id: int, name: str) -> BaseModel:
        """Download JSON from Zenodo and parse into an instance."""
        path = self.get_json(client=client, record_id=record_id, name=name)
        return self.from_json(path, client=client)

    @classmethod
    def to_json(self, path: Union[str, None] = None) -> str:
        """Serialize the average to JSON. If path is given, write to that file and return the path;
        otherwise return the JSON string. The `client` attribute is excluded from the output.
        """
        j = self.model_dump_json()
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(j)
            return path
        return j
