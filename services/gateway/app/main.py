from fastapi import FastAPI
from app.routers.api import router

app = FastAPI(title="API Generator Gateway")
app.include_router(router, prefix="/api")