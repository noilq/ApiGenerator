from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from shared.models import TableModel

class GeneratorRequest(BaseModel):
    type: str = Field(
        ..., 
        description="input type, e.g. sqlite, json, postgres",
        json_schema_extra={"example": "sqlite"}
    )
    content: List[TableModel] = Field(
        ..., 
        description="normalized table data from normalizer service"
    )
    options: Optional[Dict[str, Any]] = Field(
        default_factory=None,
        description="optional generation parameters, overrides GeneratorConfig defaults"
    )

class GeneratorResponse(BaseModel):
    files: Dict[str, str] = Field(
        ..., 
        description="generated files as filename -> content"
    )
    status: str = Field(
        default="success",
        description="generation status"
    )

class AuthConfig(BaseModel):
    enabled: bool = False
    strategy: str = "jwt"     # jwt, session, oauth2

class CiCdConfig(BaseModel):
    enabled: bool = False
    platform: str = "github_actions"    # github_actions, gitlab_ci, jenkins

class GeneratorConfig(BaseModel):
    project_name: str = "project"
    language: str = "python"
    framework: str = "fastapi"
    orm: str = "sqlalchemy"
    version: str = "v1_0"
    db_type: str = "sqlite"
    docker: bool = True
    auth: AuthConfig = Field(default_factory=AuthConfig)
    ci_cd: CiCdConfig = Field(default_factory=CiCdConfig)

    @property
    def template_path(self) -> str:
        # assembles template directory path e.g. python/fastapi/sqlalchemy/v1_0
        return f"{self.language}/{self.framework}/{self.orm}/{self.version}"
    