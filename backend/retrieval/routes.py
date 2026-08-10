from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel
from auth.jwt import get_current_user
from limit.rate_limiter import check_daily_limit

router = APIRouter(prefix="/search",
    tags=["search"],
    dependencies=[Depends(get_current_user)])

class SearchRequest(BaseModel):
    query: str

@router.post("/")
def search(data: SearchRequest, request: Request, response: Response):
    from retrieval.hybrid_search import hybrid_search
    user_id = get_current_user(request, response)

    allowed, remaining, limit = check_daily_limit(user_id, "doc_search")
    if not allowed:
        raise HTTPException(status_code=429, detail=f"Daily doc search limit reached ({limit}/day). Upgrade to Pro for unlimited.")

    chunks = hybrid_search(data.query, user_id)
    if not chunks:
        return {"results": [], "message": "No results found"}

    return {"query": data.query, "results": chunks, "remaining": remaining}