from pydantic import BaseModel, Field
from typing import List
from shared.models import TableModel

class NormalizerRequest(BaseModel):
    source_type: str = Field(
        ..., 
        description="input type, e.g. sqlite, json, postgres",
        json_schema_extra={"example": "sqlite"}
    )   # TODO: should be removed later if remains unnecessary
    tables: List[TableModel]

class NormalizerResponse(BaseModel):
    tables: List[TableModel]