from fastapi import APIRouter, UploadFile, File, Request, Response
from pydantic import BaseModel
from auth.jwt import get_current_user
from ingestion.pdf import ingest_pdf
from ingestion.website import ingest_website
from ingestion.youtube import ingest_youtube
from ingestion.ocr import ingest_image
from ingestion.document import ingest_word, ingest_text
from ingestion.csv import ingest_csv

router = APIRouter(prefix="/ingest", tags=["ingestion"])

class URLRequest(BaseModel):
    url: str

@router.post("/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    request: Request = None,
    response: Response = None
):
    user_id = get_current_user(request, response)
    file_bytes = await file.read()
    return ingest_pdf(file_bytes, file.filename, user_id)

@router.post("/website")
def upload_website(
    data: URLRequest,
    request: Request,
    response: Response
):
    user_id = get_current_user(request, response)
    return ingest_website(data.url, user_id)

@router.post("/youtube")
def upload_youtube(
    data: URLRequest,
    request: Request,
    response: Response
):
    user_id = get_current_user(request, response)
    return ingest_youtube(data.url, user_id)

