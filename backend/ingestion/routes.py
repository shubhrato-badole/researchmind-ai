from fastapi import APIRouter, UploadFile, File, Request, Response, HTTPException
from pydantic import BaseModel
from auth.jwt import get_current_user
from fastapi import Depends
from ingestion.s3_utils import upload_file_to_s3, generate_presigned_url, delete_file_from_s3
from database.postgres import get_connection
import uuid

router = APIRouter(prefix="/ingest", tags=["ingestion"],
    dependencies=[Depends(get_current_user)])

MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv", "png", "jpg", "jpeg", "pptx", "md"}

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
        raise HTTPException(status_code=400, detail=f"File type .{ext} not supported")

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 20MB.")

    
    s3_key = f"user_{user_id}/{uuid.uuid4()}_{file.filename}"
    upload_file_to_s3(file_bytes, s3_key)

    
    if ext == "pdf":
        from ingestion.pdf import ingest_pdf
        result = ingest_pdf(file_bytes, file.filename, user_id)
    elif ext == "docx":
        from ingestion.document import ingest_word
        result = ingest_word(file_bytes, file.filename, user_id)
    elif ext == "txt":
        from ingestion.document import ingest_text
        result = ingest_text(file_bytes, file.filename, user_id)
    elif ext == "csv":
        from ingestion.csv import ingest_csv
        result = ingest_csv(file_bytes, file.filename, user_id)
    elif ext in ["png", "jpg", "jpeg"]:
        from ingestion.ocr import ingest_image
        result = ingest_image(file_bytes, file.filename, user_id)
    elif ext == "pptx":
        from ingestion.pptx import ingest_pptx
        result = ingest_pptx(file_bytes, file.filename, user_id)
    elif ext == "md":
        from ingestion.markdown import ingest_markdown
        result = ingest_markdown(file_bytes, file.filename, user_id)

  
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE documents SET s3_key = %s WHERE user_id = %s AND title = %s ORDER BY created_at DESC LIMIT 1",
        (s3_key, user_id, file.filename)
    )
    conn.commit()
    cur.close()
    conn.close()

    return result

@router.get("/")
def get_documents(request: Request, response: Response):
    user_id = get_current_user(request, response)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, source_type, source_url, created_at FROM documents WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    documents = [
        {"id": r[0], "title": r[1], "source_type": r[2], "source_url": r[3], "created_at": r[4].isoformat()}
        for r in rows
    ]
    return {"documents": documents}

@router.get("/{doc_id}/download")
def download_document(doc_id: int, request: Request, response: Response):
    user_id = get_current_user(request, response)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT s3_key FROM documents WHERE id = %s AND user_id = %s", (doc_id, user_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="File not available for download")
    url = generate_presigned_url(row[0])
    return {"download_url": url}

@router.delete("/{doc_id}")
def delete_document(doc_id: int, request: Request, response: Response):
    user_id = get_current_user(request, response)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT s3_key FROM documents WHERE id = %s AND user_id = %s", (doc_id, user_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    s3_key = row[0]
    if s3_key:
        delete_file_from_s3(s3_key)
    cur.execute("DELETE FROM documents WHERE id = %s AND user_id = %s", (doc_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "deleted"}

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