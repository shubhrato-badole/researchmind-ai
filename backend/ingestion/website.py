from langchain_community.document_loaders import WebBaseLoader
from ingestion.utils import process_and_store


def ingest_website(url:str , user_id:int):
    loader = WebBaseLoader(url)
    docs= loader.load()

    return process_and_store(docs , url , "website" , url , user_id)