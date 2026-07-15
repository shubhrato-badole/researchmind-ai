from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from auth.jwt import get_current_user
from agent.graph import run_agent, stream_agent, resume_agent
from agent.memory import get_chat_history, get_sessions, create_session, update_session_title
from database.postgres import get_connection

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(get_current_user)]
)

class ChatRequest(BaseModel):
    query: str
    search_mode: str = "docs_web"
    stream: bool = False
    session_id: Optional[int] = None

class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool

class NewSessionRequest(BaseModel):
    title: str = "New chat"

@router.post("/session")
def new_session(data: NewSessionRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    session_id = create_session(user_id)
    return {"session_id": session_id}

@router.get("/sessions")
def list_sessions(request: Request, response: Response):
    user_id = get_current_user(request, response)
    return {"sessions": get_sessions(user_id)}

@router.post("/")
def chat(data: ChatRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)

    # map search_mode to search_web bool
    search_web = data.search_mode in ["docs_web", "web"]

    # create session if none
    session_id = data.session_id
    if not session_id:
        session_id = create_session(user_id)
        update_session_title(session_id, data.query[:50])

    if data.stream:
        def generate():
            for token in stream_agent(
                data.query, user_id, search_web, session_id
            ):
                yield token
        return StreamingResponse(generate(), media_type="text/plain")

    result = run_agent(data.query, user_id, search_web, session_id)
    result["session_id"] = session_id
    return result

@router.post("/resume")
def resume(data: ResumeRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    result = resume_agent(user_id, data.approved)
    return result

@router.get("/history")
def get_history(
    request: Request,
    response: Response,
    session_id: Optional[int] = None
):
    user_id = get_current_user(request, response)
    history = get_chat_history(user_id, session_id)
    return {"history": history}

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    request: Request,
    response: Response
):
    user_id = get_current_user(request, response)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM chat_sessions WHERE id = %s AND user_id = %s",
        (session_id, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Session deleted"}

@router.delete("/history")
def clear_history(request: Request, response: Response):
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