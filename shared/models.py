from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal

class ForeignKeyModel(BaseModel):
    name: Optional[str] = None # FK name in the db
    constrained_columns: List[str] # columns in current table (supports composite keys)
    referred_schema: Optional[str] = None # schema of referred table
    referred_table: str # referred table name
    referred_columns: List[str] # columns in referred table
    on_delete: str = "NO ACTION" # e.g. CASCADE, SET NULL, RESTRICT, NO ACTION
    on_update: str = "NO ACTION" # e.g. CASCADE, SET NULL, RESTRICT, NO ACTION

class IndexModel(BaseModel):
    name: str # unique index name in the db
    columns: List[str] # columns included in index (supports composite indexes)
    unique: bool = False # whether index unique
    method: str = "btree" # btree (default), hash, gin (for JSON), gist (for geo)

class PartitionModel(BaseModel):
    strategy: Literal["RANGE", "LIST", "HASH"] # partitioning model
    columns: List[str] # columns used to partition the table

class ColumnModel(BaseModel):
    name: str
    type: str # normalized type e.g. integer, datetime, - used for app logic
    raw_type: str # original type from db e.g. varchar(255) - used for app logic
    is_nullable: bool = True
    is_primary: bool = False
    is_unique: bool = False
    is_autoincrement: bool = False
    default: Optional[Any] = None # default value, could be string, integer or SQL expression like .now()
    max_length: Optional[int] = None # character limit - mainly for varchar
    precision: Optional[int] = None # total number of digits - for decimal and numeric
    scale: Optional[int] = None # digits after decimal point - for decimal and numeric
    collation: Optional[str] = None # string comparison rules like utf8mb4_bin etc.
    comment: Optional[str] = None # field description for db-level documentation
    check_constraint: Optional[str] = None # validation expression e.g. x>0

class TableModel(BaseModel):
    name: str
    schema_name: str = "public" # db namespace / schema
    columns: List[ColumnModel]
    primary_key: List[str] = Field(default_factory=list)
    indexes: List[IndexModel] = Field(default_factory=list)
    foreign_keys: List[ForeignKeyModel] = Field(default_factory=list)
    partition_by: Optional[PartitionModel] = None # partitioning config
    engine: Optional[str] = None # table storage engine e.g. innodb or idk any other tbh
    tablespace: Optional[str] = None # physical storage location
    comment: Optional[str] = None # table description