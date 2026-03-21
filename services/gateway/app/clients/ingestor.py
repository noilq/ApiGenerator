import httpx
import os 

INGESTOR_URL = os.getenv("INGESTOR_URL")

async def ingest(source_type, content):
    async with httpx.AsyncClient() as client:
        request = {"source_type": source_type, "content": content}
        response = await client.post(INGESTOR_URL, json = request, timeout = 10.0)  #10?
        response.raise_for_status()
        return response.json()