from fastapi import FastAPI, HTTPException
from app.generator import Generator
from app.models import GeneratorRequest, GeneratorResponse

import logging
from shared.logging_config import configure_logging
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Generator Service")
generator = Generator()

@app.post("/generate", response_model=GeneratorResponse)
async def generate(request: GeneratorRequest):
    logger.info("Generate request received for type: %s", request.type)
    try:
        result = await generator.generate(request.type, request.content, request.options)
        logger.info("Generation successful, files generated: %d", len(result.files))
        return result
    except ValueError as e:
        logger.warning("Invalid generation request: %s", str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during generation")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/health")
async def health():
    return {"status": "ok"}