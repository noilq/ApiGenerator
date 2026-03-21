from pydantic import BaseModel, Field
from typing import List
from shared.models import TableModel

class IngestionRequest(BaseModel):
    source_type: str = Field(
        ..., 
        description="input type, e.g. sqlite, json, postgres",
        json_schema_extra={"example": "sqlite"}
    )
    content: str = Field(
        ..., 
        description="SQL DDL dump schema",
        json_schema_extra={"example": "CREATE TABLE test (id INT);"}
    )

class IngestionResponse(BaseModel):
    tables: List[TableModel]