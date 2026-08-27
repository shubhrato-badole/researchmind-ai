from langchain_community.document_loaders import YoutubeLoader
from ingestion.utils import process_and_store


def ingest_youtube(url: str, user_id: int):
    try:
        loader = YoutubeLoader.from_youtube_url(
            url,
            add_video_info=True
        )

        docs = loader.load()

        if not docs:
            return {
                "message": "No transcript found for this YouTube video",
                "chunks": 0
            }

        return process_and_store(
            docs, url, "youtube", url, user_id
        )

    except Exception as e:
        return {
            "message": f"Unable to process YouTube video: {str(e)}",
            "chunks": 0
        }