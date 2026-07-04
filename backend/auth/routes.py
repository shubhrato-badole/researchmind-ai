from fastapi import APIRouter, HTTPException , Response, Request
from pydantic import BaseModel
from auth.jwt import create_refresh_token , create_access_token , verify_token
from database.postgres import get_connection
import bcrypt


router = APIRouter(prefix="/auth" , tags=["auth"]) 

class SignupRequest(BaseModel):
    name: str
    email:str
    password:str
    captcha_token: str

class LoginResuest(BaseModel):
    email: str
    pasword:str
    captcha_token: str

@router.post("/signup")
def signup(data:SignupRequest, response: Response):

    is_human = await verify_captcha(data.captcha_token)

    if not is_human:
        raise HTTPException(status_code=400, detail="Captcha verification failed")
    
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

@router.post("/login")
def login(data: LoginResuest, response:Response):
     connection  = get_connection()
     cur= connection.cursor()

     cur.execute("SELECT * FROM users WHERE email=%s" , (data.email))
     user = cur.fetchone()
     cur.close()
     connection.close()

     if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

     user_id, name, hashed_password = user


     if not bcrypt.checkpw(data.password.encode(), hashed_password.encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")
      
     access_token = create_access_token(user_id)
     refresh_token = create_refresh_token(user_id)
     save_refresh_token(user_id, refresh_token)

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

     return {"user": {"id": user_id, "name": name, "email": data.email}}


@router.post("/refresh")
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    user_id = verify_token(refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

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
        raise HTTPException(status_code=401, detail="Session not found")

    access_token = create_access_token(user_id)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,
        samesite="lax"
    )
    return {"message": "Token refreshed"}




@router.post("/logout")
def logout(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM sessions WHERE refresh_token = %s", (refresh_token,))
        conn.commit()
        cur.close()
        conn.close()

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}