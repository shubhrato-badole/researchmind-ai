from fastapi import APIRouter, Request, Response
from agent.graph import run_agent , resume_agent 
from pydantic import BaseModel
from auth.jwt import get_current_user
from agent.graph import run_agent, stream_agent, resume_agent
from agent.memory import save_message, get_chat_history
from fastapi.responses import StreamingResponse
from fastapi import Depends

router = APIRouter(prefix="/chat", tags=["chat"],
                   dependencies=[Depends(get_current_user)])


class ChatRequest(BaseModel):
    query: str
    search_web: bool = False
    stream: bool = False

class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool

@router.post("/")
def chat(data: ChatRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)

    if data.stream:
        def generate():
            for token in stream_agent(data.query, user_id, data.search_web):
                yield token

        return StreamingResponse(generate(), media_type="text/plain")
    result = run_agent(data.query, user_id, data.search_web)
    return result
    

@router.post("/resume")
def resume(data: ResumeRequest, request: Request, response: Response):
     user_id = get_current_user(request, response)
     result = resume_agent(user_id, data.approved)
     return result
    
@router.get("/history")
def get_history(request: Request, response: Response):
     user_id = get_current_user(request, response)
     history = get_chat_history(user_id)
     return {"history": history}


@router.delete("/history")
def clear_history(request: Request, response: Response):
    from database.postgres import get_connection
    user_id = get_current_user(request, response)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM chat_history WHERE user_id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "History cleared"}