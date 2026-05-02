# backend/app/main.py
from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="DocuMind AI")

app.include_router(api_router)


@app.get("/")
def root():
    return {"message": "DocuMind AI running"}
