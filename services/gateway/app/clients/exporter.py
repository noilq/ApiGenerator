import httpx
import os

EXPORTER_URL = os.getenv("EXPORTER_URL")

async def export(project_name, files):
    async with httpx.AsyncClient() as client:
        request = {"project_name": project_name, "files": files}
        response = await client.post(EXPORTER_URL, json=request, timeout=10.0)  #10?
        response.raise_for_status()
        return response.json()