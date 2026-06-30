from fastapi import APIRouter, UploadFile, File, Request, Response, HTTPException
from pydantic import BaseModel
from auth.jwt import get_current_user
from ingestion.pdf import ingest_pdf
from ingestion.website import ingest_website
from ingestion.youtube import ingest_youtube
from ingestion.ocr import ingest_image
from ingestion.document import ingest_word, ingest_text
from ingestion.csv import ingest_csv
from ingestion.pptx import ingest_pptx
from ingestion.markdown import ingest_markdown
from fastapi import Depends

router = APIRouter(prefix="/ingest", tags=["ingestion"],
                   dependencies=[Depends(get_current_user)])


MAX_FILE_SIZE = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "pdf", "docx", "txt", "csv", "png",
    "jpg", "jpeg", "pptx", "md"
}

class URLRequest(BaseModel):
    url: str

def get_extension(filename: str):
    return filename.rsplit(".", 1)[-1].lower()

@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    request: Request = None,
    response: Response = None
):
    user_id = get_current_user(request, response)
    ext = get_extension(file.filename)

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{ext} not supported"
        )

    file_bytes = await file.read()

    
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size is 20MB."
        )

    if ext == "pdf":
        return ingest_pdf(file_bytes, file.filename, user_id)
    elif ext == "docx":
        return ingest_word(file_bytes, file.filename, user_id)
    elif ext == "txt":
        return ingest_text(file_bytes, file.filename, user_id)
    elif ext == "csv":
        return ingest_csv(file_bytes, file.filename, user_id)
    elif ext in ["png", "jpg", "jpeg"]:
        return ingest_image(file_bytes, file.filename, user_id)
    elif ext == "pptx":
        return ingest_pptx(file_bytes, file.filename, user_id)
    elif ext == "md":
        return ingest_markdown(file_bytes, file.filename, user_id)

@router.post("/website")
def upload_website(data: URLRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return ingest_website(data.url, user_id)

@router.post("/youtube")
def upload_youtube(data: URLRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)
    return ingest_youtube(data.url, user_id)