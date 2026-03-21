import httpx
import os

GENERATOR_URL = os.getenv("GENERATOR_URL")

async def generate(type, data, options):
    async with httpx.AsyncClient() as client:
        request = {"type": type, "content": data, "options": options}
        response = await client.post(GENERATOR_URL, json=request, timeout=10.0)  #10?
        response.raise_for_status()
        return response.json()