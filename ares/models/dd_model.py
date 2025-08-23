from enum import Enum
from typing import Literal, Union, List, Dict, TypeAlias, Annotated
from pydantic import BaseModel, Field, RootModel


class Datatype(str, Enum):
    float = "float"
    double = "double"
    bool = "bool"
    short = "short"
    int = "int"
    long = "long"
    longlong = "longlong"
    uint = "uint"
    ulong = "ulong"
    ulonglong = "ulonglong"

Size = List[int]
InputAlternatives: TypeAlias = List[Union[str, float, List[float]]]

class BaseDDModel(BaseModel):
    datatype: Datatype
    size: Size

    class Config:
        extra = "forbid"

class InModel(BaseDDModel):
    type: Literal["in"]
    input_alternatives: Union[InputAlternatives, None] = None

class InoutModel(BaseDDModel):
    type: Literal["inout"]
    input_alternatives: Union[InputAlternatives, None] = None

class OutModel(BaseDDModel):
    type: Literal["out"]

DDElement = Union[InModel, InoutModel, OutModel]

# Die finale, korrekte Definition für ein "flaches" Dictionary
class DataDictionary(RootModel):
    root: Dict[Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]+$")], DDElement]

    def __getitem__(self, key):
        return self.root[key]

    def items(self):
        return self.root.items()

    def values(self):
        return self.root.values()

    def keys(self):
        return self.root.keys()
