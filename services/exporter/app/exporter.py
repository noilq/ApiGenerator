from pathlib import Path
from app.models import ExporterResponse
import shutil

BASE_DIR = Path("/app/generated_projects")

class Exporter:
    def __init__(self):
        self.base_output_dir = BASE_DIR
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    async def export(self, project_name: str, files: dict) -> ExporterResponse:
        safe_name = project_name.replace(" ", "_").lower()

        project_path = self.base_output_dir / safe_name
        if project_path.exists():       # wipe folder before
            shutil.rmtree(project_path)
        project_path.mkdir(parents=True, exist_ok=True)

        for rel_path, content in files.items():
            file_path = project_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        return ExporterResponse(
            path_saved_to=str(project_path),
            url_to_download_repo=f"http://localhost:8000/api/{safe_name}/download",
            url_to_browse_repo=f"http://localhost:8000/api/{safe_name}/files",
            url_localhost_repo="NOT IMPLEMENTED"
        )
    
    