# backend/app/main.py
from fastapi import FastAPI
from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_chat import router as chat_router
from app.api.v1.routes_upload import router as upload_router
from app.api.v1.routes_ingest import router as ingest_router
from app.api.v1.routes_query import router as query_router
app = FastAPI(title="DocuMind AI")

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(upload_router)
@app.get("/")
def root():
    return {"message": "DocuMind AI running"}