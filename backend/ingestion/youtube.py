from langchain_community.document_loaders import YoutubeLoader
from ingestion.utils import process_and_store


def ingest_youtube(url:str , user_id:int):
    loader =  YoutubeLoader.from_youtube_url(url, add_video_info=True)
    docs = loader.load()

    return process_and_store(docs, url, "youtube", url, user_id)