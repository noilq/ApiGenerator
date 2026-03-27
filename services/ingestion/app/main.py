from fastapi import FastAPI, HTTPException
from app.models import IngestionRequest, IngestionResponse
from app.strategy import Ingestor

import logging
from shared.logging_config import configure_logging
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Ingestion Service")
ingestor = Ingestor()

@app.post("/ingest", response_model=IngestionResponse)
async def ingest_schema(request: IngestionRequest):
    logger.info("Ingest request received for type: %s", request.source_type)
    try:
        result =  await ingestor.process_schema(request.source_type, request.content)
        logger.info("Ingestion successful, tables parsed: %d", len(result.tables))
        return result
    except ValueError as e:
        logger.warning("Unsupported input type requested: %s", request.source_type)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during ingestion")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/health")
async def health():
    return {"status": "ok"}