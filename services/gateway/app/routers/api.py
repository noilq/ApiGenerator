import io
import zipfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from app.models import GenerateRequest
from app.orchestration import run_pipeline

router = APIRouter()


@router.post("/generate")
async def generate(request: GenerateRequest):
    return await run_pipeline(request)



BASE = Path("generated_projects")

@router.get("/{project_name}/download", summary="Download project as ZIP")
async def download_project(project_name: str):
    project_path = BASE / project_name
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in project_path.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(project_path))
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={project_name}.zip"},
    )
    
@router.get("/{project_name}/view", response_class=HTMLResponse)
async def view_project(project_name: str):
    project_path = BASE / project_name
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    items = []

    for f in sorted(project_path.rglob("*")):
        rel = f.relative_to(project_path)
        indent = "&nbsp;" * (len(rel.parts) - 1) * 4
        
        if f.is_file():
            file_path = rel.as_posix()
            items.append(
                f'<div>{indent}<a href="/api/{project_name}/files/{file_path}">{f.name}</a></div>'
            )
        else:
            items.append(
                f'<div>{indent}<b>{f.name}/</b></div>'
            )

    content = "".join(items)
    
    return f"""
    <html>
        <body>
            <h3>{project_name}</h3>
            <a href="/api/{project_name}/download">[Download ZIP]</a>
            {content}
        </body>
    </html>
    """