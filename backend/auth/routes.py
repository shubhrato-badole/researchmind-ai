from fastapi import APIRouter, HTTPException , Response, Request
from pydantic import BaseModel
from auth.jwt import create_refresh_token , create_access_token
from database.postgres import get_connection
import bcrypt

router = APIRouter(prefix="/auth" , tags=["auth"]) 

class SignupRequest(BaseModel):
    name: str
    email:str
    password:str

class LoginResuest(BaseModel):
    email: str
    pasword:str

@router.post("/signup")
def signup(data:SignupRequest, response: Response):
    connection = get_connection()
    cur = connection.cursor()
     
    cur.execute("SELECT id FROM users WHERE email=%s", (data.email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashpassword= bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    cur.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id",
        (data.name, data.email, hashpassword)
    )

    user_id = cur.fetchone()[0]
    connection.commit()
    cur.close()
    connection.close()

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,       
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=604800,     
        samesite="lax"
    )

    return {"user": {"id": user_id, "name": data.name, "email": data.email}}

