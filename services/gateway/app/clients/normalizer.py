import httpx
import os

NORMALIZER_URL = os.getenv("NORMALIZER_URL")

async def normalize(source_type, content):
    async with httpx.AsyncClient() as client:
        request = {"source_type": source_type, "tables": content}
        response = await client.post(NORMALIZER_URL, json=request, timeout=10.0)  #10?
        response.raise_for_status()
        return response.json()