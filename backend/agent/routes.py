from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import logging
from auth.jwt import get_current_user
from database.postgres import get_connection

logger = logging.getLogger(__name__)

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
    session_id: Optional[int] = None

class NewSessionRequest(BaseModel):
    title: str = "New chat"


@router.post("/session")
def new_session(data: NewSessionRequest, request: Request, response: Response):
    from agent.memory import create_session
    user_id = get_current_user(request, response)
    session_id = create_session(user_id)
    return {"session_id": session_id}


@router.get("/sessions")
def list_sessions(request: Request, response: Response):
    from agent.memory import get_sessions
    user_id = get_current_user(request, response)
    return {"sessions": get_sessions(user_id)}


@router.post("/")
def chat(data: ChatRequest, request: Request, response: Response):
    from agent.memory import update_session_title, create_session
    from agent.graph import run_agent, stream_agent

    user_id = get_current_user(request, response)

    session_id = data.session_id
    if not session_id:
        session_id = create_session(user_id)
        update_session_title(session_id, data.query[:50])

    if data.stream:
        def generate():
            try:
                yield from stream_agent(
                    data.query,
                    user_id,
                    data.search_mode,
                    session_id,
                )
            except Exception:
                # Streaming headers have already been sent, so return a readable
                # message rather than abruptly closing the response body.
                logger.exception("Streaming chat generation failed")
                yield "\n\n⚠️ The response was interrupted while generating. Please try again."

        return StreamingResponse(
            generate(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )

    result = run_agent(data.query, user_id, data.search_mode, session_id)
    result["session_id"] = session_id
    return result


@router.post("/resume")
def resume(data: ResumeRequest, request: Request, response: Response):
    from agent.graph import resume_agent
    user_id = get_current_user(request, response)
    result = resume_agent(user_id, data.approved, data.session_id)
    return result


@router.get("/history")
def get_history(
    request: Request,
    response: Response,
    session_id: Optional[int] = None
):
    from agent.memory import get_chat_history
    user_id = get_current_user(request, response)
    history = get_chat_history(user_id, session_id)
    return {"history": history}


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    request: Request,
    response: Response
):
    """Delete one owned chat and its messages, even if legacy FK cascade is absent."""
    user_id = get_current_user(request, response)
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Explicit child-row delete supports databases created before ON DELETE CASCADE.
        cur.execute(
            "DELETE FROM chat_history WHERE session_id = %s AND user_id = %s",
            (session_id, user_id)
        )
        cur.execute(
            "DELETE FROM chat_sessions WHERE id = %s AND user_id = %s RETURNING id",
            (session_id, user_id)
        )
        deleted = cur.fetchone()
        if deleted is None:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Chat not found")
        conn.commit()
        return {"message": "Session deleted", "session_id": session_id}
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        logger.exception("Failed to delete chat session %s for user %s", session_id, user_id)
        raise HTTPException(status_code=500, detail="Could not delete chat. Please try again.")
    finally:
        cur.close()
        conn.close()


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