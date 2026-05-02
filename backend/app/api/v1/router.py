from fastapi import APIRouter

from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.ingest import router as ingest_router
from app.api.v1.endpoints.query import router as query_router
from app.api.v1.endpoints.upload import router as upload_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(ingest_router)
api_router.include_router(query_router)
api_router.include_router(upload_router)

