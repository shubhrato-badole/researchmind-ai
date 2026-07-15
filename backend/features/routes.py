from fastapi import APIRouter, Request, Response, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from auth.jwt import get_current_user
from features.study_mode import (
    generate_quiz,
    check_answer,
    save_score,
    get_score_history,
    get_weak_topics,
    get_user_topics,
    generate_flashcards,
    generate_summary,
    generate_interview_question,
    evaluate_interview_answer
)
from features.voice_query import transcribe_voice
# from features.evaluation import evaluate_rag
from agent.graph import run_agent

router = APIRouter(
    prefix="/features",
    tags=["features"],
    dependencies=[Depends(get_current_user)]
)

class QuizRequest(BaseModel):
    num_questions: int = 5
    difficulty: str = "medium"
    topic: Optional[str] = None

class AnswerRequest(BaseModel):
    selected: int
    correct: int
    explanation: str

class ScoreRequest(BaseModel):
    score: int
    total: int
    topic: Optional[str] = None
    difficulty: str = "medium"

@router.post("/quiz")
def get_quiz(data: QuizRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return generate_quiz(user_id, data.num_questions, data.difficulty, data.topic)

@router.post("/quiz/check")
def check_quiz_answer(data: AnswerRequest):
    return check_answer(data.selected, data.correct, data.explanation)

@router.post("/quiz/score")
def submit_score(data: ScoreRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return save_score(user_id, data.score, data.total, data.topic, data.difficulty)

@router.get("/quiz/history")
def quiz_history(request: Request, response: Response):
    user_id = get_current_user(request, response)
    return {"history": get_score_history(user_id)}

@router.get("/quiz/weak-topics")
def weak_topics(request: Request, response: Response):
    user_id = get_current_user(request, response)
    return {"weak_topics": get_weak_topics(user_id)}



@router.get("/topics")
def topics(
    request: Request,
    response: Response,
    document_ids: str = None  
):
    from database import get_connection
    user_id = get_current_user(request, response)

    if document_ids:
        ids = [int(i) for i in document_ids.split(',')]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """SELECT DISTINCT topic FROM document_topics
               WHERE user_id = %s AND document_id = ANY(%s)
               ORDER BY topic""",
            (user_id, ids)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"topics": [r[0] for r in rows]}

    
    return {"topics": get_user_topics(user_id)}


class FlashcardRequest(BaseModel):
    topic: Optional[str] = None
    count: int = 10

@router.post("/flashcards")
def flashcards(data: FlashcardRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return generate_flashcards(user_id, data.topic, data.count)



class SummaryRequest(BaseModel):
    topic: Optional[str] = None

@router.post("/summary")
def summary(data: SummaryRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return generate_summary(user_id, data.topic)



class InterviewRequest(BaseModel):
    topic: Optional[str] = None


@router.post("/interview/question")
def interview_question(data: InterviewRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return generate_interview_question(user_id, data.topic)



@router.post("/voice")
async def voice_search(
    file: UploadFile = File(...),
    request: Request = None,
    response: Response = None
):
    user_id = get_current_user(request, response)
    audio_bytes = await file.read()
    result = transcribe_voice(audio_bytes, file.filename)
    if "error" in result:
        return result
    answer = run_agent(result["text"], user_id)
    return {"transcribed": result["text"], "answer": answer}



class EvalRequest(BaseModel):
    query: str

# @router.post("/evaluate")
# def evaluate(data: EvalRequest, request: Request, response: Response):
#     user_id = get_current_user(request, response)
#     return evaluate_rag(data.query, user_id)