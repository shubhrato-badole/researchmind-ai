# ingestion/utils.py
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document
from database.chromadb import get_collection
from database.postgres import get_connection
from config import GEMINI_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP

def process_and_store(
    docs: list,
    filename: str,
    source_type: str,
    source_url: str,
    user_id: int
):
    try:
       
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.split_documents(docs)

        if not chunks:
            return {"message": "No content found", "chunks": 0}

       
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=GEMINI_API_KEY
        )

       
        collection = get_collection(str(user_id))

        for i, chunk in enumerate(chunks):
            embedding = embeddings_model.embed_query(chunk.page_content)
            collection.add(
                ids=[f"{source_type}_{filename}_{i}"],
                embeddings=[embedding],
                documents=[chunk.page_content],
                metadatas=[{
                    "source_type": source_type,
                    "filename": filename,
                    "source_url": source_url or "",
                    "user_id": str(user_id)
                }]
            )

   
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO documents (user_id, title, source_type, source_url) VALUES (%s, %s, %s, %s)",
            (user_id, filename, source_type, source_url)
        )
        conn.commit()
        cur.close()
        conn.close()

        return {
            "message": f"{source_type} ingested successfully",
            "chunks": len(chunks)
        }

    except Exception as e:
        return {"message": f"Error: {str(e)}", "chunks": 0}