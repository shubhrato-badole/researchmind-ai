
from fastapi import APIRouter, Request, Response, Depends
from pydantic import BaseModel
from auth.jwt import get_current_user
from roadmap.roadmap import (
    generate_roadmap,
    start_step,
    complete_step,
    get_progress,
    get_user_roadmaps
)

router = APIRouter(
    prefix="/roadmap",
    tags=["roadmap"],
    dependencies=[Depends(get_current_user)]
)

class RoadmapRequest(BaseModel):
    goal: str
    current_knowledge: str = "beginner"

class StepRequest(BaseModel):
    roadmap_id: int
    step_number: int

class CompleteStepRequest(BaseModel):
    roadmap_id: int
    step_number: int
    quiz_passed: bool

@router.post("/")
def create_roadmap(data: RoadmapRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return generate_roadmap(data.goal, data.current_knowledge, user_id)

@router.get("/")
def my_roadmaps(request: Request, response: Response):
    user_id = get_current_user(request, response)
    return {"roadmaps": get_user_roadmaps(user_id)}

@router.post("/start-step")
def start_roadmap_step(data: StepRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return start_step(data.roadmap_id, data.step_number, user_id)

@router.post("/complete-step")
def complete_roadmap_step(data: CompleteStepRequest):
    return complete_step(data.roadmap_id, data.step_number, data.quiz_passed)

@router.get("/{roadmap_id}/progress")
def roadmap_progress(roadmap_id: int, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return get_progress(roadmap_id, user_id)