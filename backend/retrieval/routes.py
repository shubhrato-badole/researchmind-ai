from http.client import HTTPException
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from auth.jwt import get_current_user
from fastapi import Depends
from limit.rate_limiter import check_daily_limit

router = APIRouter(prefix="/search",
                    tags=["search"],
                   dependencies=[Depends(get_current_user)]  )

class SearchRequest(BaseModel):
    query: str

@router.post("/")
def search(
    data: SearchRequest,
    request: Request,
    response: Response
):
    from retrieval.hybrid_search import hybrid_search
    # from retrieval.reranker import rerank
    user_id = get_current_user(request, response)
    chunks = hybrid_search(data.query, user_id)
    allowed, remaining, limit = check_daily_limit(user_id, "doc_search")
    if not allowed:
        raise HTTPException(status_code=429, detail=f"Daily doc search limit reached ({limit}/day). Upgrade to Pro for unlimited.")

    if not chunks:
        return {"results": [], "message": "No results found"}

    # results = rerank(data.query, chunks)
    results = chunks

    return {
        "query": data.query,
        "results": results,
         "remaining": remaining
    }