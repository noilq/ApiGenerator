from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal, Dict

class ExporterRequest(BaseModel):
    project_name: str
    files: Dict[str, str] = Field(
        ..., 
        description="Generated code {'filename': 'text'}"
    )

class ExporterResponse(BaseModel):
    path_saved_to: str = Field()
    url_to_download_repo: str = Field()
    url_to_browse_repo: str = Field()
    url_localhost_repo: str = Field()