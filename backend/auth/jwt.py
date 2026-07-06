from jose import jwt
from datetime import datetime, timedelta
from config import JWT_SECRET
from fastapi import Request, HTTPException , Response
from database.postgres import get_connection

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
    
def get_current_user(request: Request, response: Response):
   
    access_token = request.cookies.get("access_token")
    if access_token:
        user_id = verify_token(access_token)
        if user_id:
            return user_id

   
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = verify_token(refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired, please login again")

   
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM sessions WHERE refresh_token = %s AND user_id = %s",
        (refresh_token, user_id)
    )
    session = cur.fetchone()
    cur.close()
    conn.close()

    if not session:
        raise HTTPException(status_code=401, detail="Session not found, please login again")

   
    new_access_token = create_access_token(user_id)
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=1800,
        samesite="lax"
    )

    return user_id