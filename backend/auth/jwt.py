from jose import jwt
from datetime import datetime, timedelta
from config import JWT_SECRET
from fastapi import Request, HTTPException

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES= 30
REFRESH_TOKEN_EXPIRE_DAYS= 7

def create_access_token(user_id:int):
    payload={
        "user_id":user_id,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload , JWT_SECRET, algorithm=ALGORITHM)

def create_refresh_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except:
        return None
    
def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id