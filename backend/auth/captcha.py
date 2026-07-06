import httpx
from config import RECAPTCHA_SECRET_KEY

async def verify_captcha(token: str) -> bool:
    if not token or not RECAPTCHA_SECRET_KEY:
        return True  

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": RECAPTCHA_SECRET_KEY,
                    "response": token
                }
            )
            result = response.json()
            return result.get("success", False) and result.get("score", 0) > 0.5
    except:
        return True  