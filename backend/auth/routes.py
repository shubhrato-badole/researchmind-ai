from fastapi import APIRouter, HTTPException , Response, Request
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from auth.jwt import create_refresh_token , create_access_token , verify_token , get_current_user
from database.postgres import get_connection
import bcrypt
from auth.goggle_auth import oauth, get_or_create_google_user
from auth.captcha import verify_captcha
from auth.otp_utils import generate_otp, save_otp, verify_otp, send_otp_email
from config import FRONTEND_URL
from slowapi import Limiter
from slowapi.util import get_remote_address
from database.postgres import get_connection

router = APIRouter(prefix="/auth" , tags=["auth"]) 
limiter = Limiter(key_func=get_remote_address)

class SignupRequest(BaseModel):
    name: str
    email:str
    password:str
    captcha_token: str

class LoginRequest(BaseModel):
    email: str
    pasword:str
    captcha_token: str

class ChangePasswordResuest(BaseModel):
     current_password: str
     new_password:str

class OTPRequest(BaseModel):
    email: str
    otp: str

class ResendOTPRequest(BaseModel):
    email: str

class RefreshRequest(BaseModel):
    pass


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token", value=access_token,
        httponly=True, max_age=1800, samesite="lax"
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, max_age=604800, samesite="lax"
    )

def save_refresh_token(user_id: int, refresh_token: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (user_id, refresh_token) VALUES (%s, %s)",
        (user_id, refresh_token)
    )
    conn.commit()
    cur.close()
    conn.close()










@router.post("/signup")
@limiter.limit("5/minute")
async def signup(request: Request, data: SignupRequest, response: Response):
  
    is_human = await verify_captcha(data.captcha_token)
    if not is_human:
        raise HTTPException(status_code=400, detail="Captcha verification failed")

    conn = get_connection()
    cur = conn.cursor()

   
    cur.execute("SELECT id, is_verified FROM users WHERE email = %s", (data.email,))
    existing = cur.fetchone()

    if existing:
        user_id, is_verified = existing
        if not is_verified:
           
            cur.close()
            conn.close()
            otp = generate_otp()
            save_otp(user_id, otp)
            send_otp_email(data.email, otp, data.name)
            return {
                "status": "unverified",
                "message": "Account exists but not verified. OTP resent.",
                "email": data.email
            }
        raise HTTPException(status_code=400, detail="Email already exists")

  
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO users (name, email, password, is_verified)
           VALUES (%s, %s, %s, FALSE) RETURNING id""",
        (data.name, data.email, hashed)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

  
    otp = generate_otp()
    save_otp(user_id, otp)
    send_otp_email(data.email, otp, data.name)

    return {
        "status": "otp_sent",
        "message": "OTP sent to your email",
        "email": data.email
    }




@router.post("/verify-otp")
async def verify_otp_route(data: OTPRequest, response: Response):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name FROM users WHERE email = %s",
        (data.email,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id, name = user

    if not verify_otp(user_id, data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

   
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    save_refresh_token(user_id, refresh_token)
    set_auth_cookies(response, access_token, refresh_token)

    return {
        "status": "verified",
        "user": {"id": user_id, "name": name, "email": data.email}
    }



@router.post("/resend-otp")
@limiter.limit("3/minute")
async def resend_otp(request: Request, data: ResendOTPRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, is_verified FROM users WHERE email = %s",
        (data.email,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id, name, is_verified = user

    if is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    otp = generate_otp()
    save_otp(user_id, otp)
    send_otp_email(data.email, otp, name)

    return {"message": "OTP resent successfully"}



@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, response: Response):
    is_human = await verify_captcha(data.captcha_token)
    if not is_human:
        raise HTTPException(status_code=400, detail="Captcha verification failed")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, password, is_verified, auth_provider FROM users WHERE email = %s",
        (data.email,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id, name, hashed_password, is_verified, auth_provider = user

 
    if auth_provider == "google":
        raise HTTPException(
            status_code=400,
            detail="This account uses Google login. Please sign in with Google."
        )

    if not bcrypt.checkpw(data.password.encode(), hashed_password.encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")


    if not is_verified:
     
        otp = generate_otp()
        save_otp(user_id, otp)
        send_otp_email(data.email, otp, name)
        return {
            "status": "unverified",
            "message": "Email not verified. OTP sent.",
            "email": data.email
        }

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    save_refresh_token(user_id, refresh_token)
    set_auth_cookies(response, access_token, refresh_token)

    return {
        "status": "success",
        "user": {"id": user_id, "name": name, "email": data.email}
    }



@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = f"{request.base_url}auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, response: Response):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        email = user_info["email"]
        name = user_info["name"]

        user_id, name = get_or_create_google_user(email, name)

        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        save_refresh_token(user_id, refresh_token)

        redirect = RedirectResponse(url=f"{FRONTEND_URL}/chat")
        redirect.set_cookie(
            key="access_token", value=access_token,
            httponly=True, max_age=1800, samesite="lax"
        )
        redirect.set_cookie(
            key="refresh_token", value=refresh_token,
            httponly=True, max_age=604800, samesite="lax"
        )
        return redirect

    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_failed")
    



@router.get("/me")
def me(request: Request, response: Response):
    user_id = get_current_user(request, response)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, auth_provider FROM users WHERE id = %s",
        (user_id,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user": {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "auth_provider": user[3]
        }
    }

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
        key="access_token", value=access_token,
        httponly=True, max_age=1800, samesite="lax"
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




@router.post("/change-password")
def change_password(
    data: ChangePasswordResuest,
    request: Request,
    response: Response
):
    user_id = get_current_user(request, response)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT password FROM users WHERE id=%s",
        (user_id,)
    )
    user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_password = user[0]

    if not bcrypt.checkpw(
        data.current_password.encode(),
        stored_password.encode()
    ):
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect"
        )

    hashed_password = bcrypt.hashpw(
        data.new_password.encode(),
        bcrypt.gensalt()
    ).decode()

    cur.execute(
        "UPDATE users SET password=%s WHERE id=%s",
        (hashed_password, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Password changed successfully"}



@router.delete("/delete-account")
def delete_account(
    request: Request,
    response: Response
):
    user_id = get_current_user(request, response)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM users WHERE id=%s",
        (user_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {
        "message": "Account deleted successfully"
    }