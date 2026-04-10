# backend/app/main.py
from fastapi import FastAPI
from app.api.v1.routes_health import router as health_router

app = FastAPI(title="DocuMind AI")

app.include_router(health_router)

@app.get("/")
def root():
    return {"message": "DocuMind AI running"}