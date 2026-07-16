# import whisper
# import tempfile
# import os

# model = None

# def get_model():
#     global model
#     if model is None:
#         model = whisper.load_model("base")
#     return model

# def transcribe_voice(audio_bytes: bytes, filename: str):
#     try:
#         ext = filename.rsplit(".", 1)[-1].lower()
#         if ext not in ["mp3", "mp4", "wav", "m4a", "ogg", "webm"]:
#             return {"error": "Unsupported audio format"}

#         with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
#             tmp.write(audio_bytes)
#             tmp_path = tmp.name

#         result = get_model().transcribe(tmp_path)
#         os.unlink(tmp_path)

#         return {"text": result["text"].strip()}

#     except Exception as e:
#         return {"error": f"Could not transcribe: {str(e)}"}