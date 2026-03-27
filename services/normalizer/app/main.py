from fastapi import FastAPI, HTTPException
from app.models import NormalizerRequest, NormalizerResponse
from app.normalizer import Normalizer

import logging
from shared.logging_config import configure_logging
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Normalization Service")
normalizer = Normalizer()

@app.post("/normalize", response_model=NormalizerResponse)
async def normalize_schema(request: NormalizerRequest):
    logger.info("Normalize request received")
    try:
        result = normalizer.normalize(request.tables)
        logger.info("Normalization successful, tables parsed: %d", len(result.tables))
        return result
    except ValueError as e:
        logger.warning("Unsupported input type requested: %s", request.source_type)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during normalization")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health():
    return {"status": "ok"}