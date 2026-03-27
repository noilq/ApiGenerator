from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# dto

class GenerateRequest(BaseModel):
    source_type: str = Field(
        ..., 
        description="Database type, eg. sqlite, postgres",
        json_schema_extra={"example": "sqlite"}
    )
    content: str = Field(
        ..., 
        description="SQL DDL",
        json_schema_extra={"example": "CREATE TABLE Customers (customer_id INTEGER PRIMARY KEY, email TEXT(128), gender TEXT CHECK(gender IN ('Male', 'Female')));"}
    )
    options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "project_name": "project",
            "language": "python",
            "framework": "fastapi",
            "orm": "sqlalchemy",
            "version": "v1_0",
            "auth": {
                "enabled": False,
                "strategy": "jwt"   
            },
            "ci_cd": {
                "enabled": False
            },
            "docker": True
        },
        description="Generation parameters",
        json_schema_extra={
            "example": {
                "project_name": "project",
                "language": "python",
                "framework": "fastapi",
                "orm": "sqlalchemy",
                "version": "v1_0",
                "auth": {
                    "enabled": False,
                    "strategy": "jwt"
                },
                "ci_cd": {
                    "enabled": False
                },
                "docker": True
            }
        }
    )

class GenerateResponse(BaseModel):  
    status: str = Field(..., description="Result, eg. success/error")
    files: Dict[str, str] = Field(..., description="Generated code {'filename': 'text'}") # {"models.py": "class User...", "main.py": "..."}
    download_url: Optional[str] = None