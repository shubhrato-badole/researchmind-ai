from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from database.chromadb import get_collection
from database.postgres import get_connection
from config import GEMINI_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP



embeddings_model  = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001" , # we are craetig an ebedding and using this model for embedding
     google_api_key=GEMINI_API_KEY
)


splitter = RecursiveCharacterTextSplitter(
    CHUNK_SIZE = CHUNK_SIZE,
 CHUNK_OVERLAP = CHUNK_OVERLAP)

def process_and_store(docs:list ,   
                      filename: str,  
                    source_type: str, 
                    source_url: str, 
                     user_id: int):
    chunks= splitter.split_document(docs)

    if not chunks:
        return {"message": "No content found", "chunks": 0}
    
    collection = get_collection

    for i , chunk in enumerate(chunks):
        embeddings= embeddings_model.embed_query(chunk.page_content)
        collection.add(
            ids=[f"{source_type}_{filename}_{i}"],
            embedding=[embeddings],
            document= [chunks.page_content],
            metadata=[{
                "source_type": source_type,
                "filename": filename,
                "source_url": source_url or "",
                "user_id": str(user_id)
            }]

        )

        conn= get_connection
        cur = conn.cursor()

        cur.execute( "INSERT INTO documents (user_id, title, source_type, source_url) VALUES (%s, %s, %s, %s)",
        (user_id, filename, source_type, source_url) )

        conn.commit()
    cur.close()
    conn.close()

    return {
        "message": f"{source_type} ingested successfully",
        "chunks": len(chunks)
    }