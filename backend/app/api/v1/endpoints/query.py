from fastapi import APIRouter
from pydantic import BaseModel

from app.services.query_service import QueryService

router = APIRouter(prefix="/query", tags=["Query"])
query_service = QueryService()


class QueryRequest(BaseModel):
    question: str


@router.post("/")
def query(req: QueryRequest):
    return query_service.query(req.question)

