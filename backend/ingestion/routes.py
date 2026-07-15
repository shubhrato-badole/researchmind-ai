
from fastapi import APIRouter, UploadFile, File, Request, Response, HTTPException
from pydantic import BaseModel
from auth.jwt import get_current_user
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
        from ingestion.pdf import ingest_pdf
        return ingest_pdf(file_bytes, file.filename, user_id)
    elif ext == "docx":
        from ingestion.document import ingest_word
        return ingest_word(file_bytes, file.filename, user_id)
    elif ext == "txt":
        from ingestion.document import  ingest_text
        return ingest_text(file_bytes, file.filename, user_id)
    elif ext == "csv":
        from ingestion.csv import ingest_csv
        return ingest_csv(file_bytes, file.filename, user_id)
    elif ext in ["png", "jpg", "jpeg"]:
        from ingestion.ocr import ingest_image
        return ingest_image(file_bytes, file.filename, user_id)
    elif ext == "pptx":
        from ingestion.pptx import ingest_pptx
        return ingest_pptx(file_bytes, file.filename, user_id)
    elif ext == "md":
        from ingestion.markdown import ingest_markdown
        return ingest_markdown(file_bytes, file.filename, user_id)

@router.post("/website")
def upload_website(data: URLRequest, request: Request, response: Response):
    from ingestion.website import ingest_website
    user_id = get_current_user(request, response)
    return ingest_website(data.url, user_id)

@router.post("/youtube")
def upload_youtube(data: URLRequest, request: Request, response: Response):
    from ingestion.youtube import ingest_youtube
    user_id = get_current_user(request, response)
    return ingest_youtube(data.url, user_id)