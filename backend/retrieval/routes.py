from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from auth.jwt import get_current_user
from fastapi import Depends

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

    if not chunks:
        return {"results": [], "message": "No results found"}

    # results = rerank(data.query, chunks)
    results = chunks

    return {
        "query": data.query,
        "results": results
    }