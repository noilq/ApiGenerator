from fastapi import FastAPI, HTTPException
from app.exporter import Exporter
from app.models import ExporterRequest

app = FastAPI(title="Exporter Service")
exporter = Exporter()

@app.post("/export")
async def export(request: ExporterRequest):
    try:
        result = await exporter.export(request.project_name, request.files)
        
        return result
    except Exception as e:
        print(f"Export failed:\n{str(e)}")
        raise HTTPException(status_code = 400, detail = f"Export failed {str(e)}")