import random
import smtplib
import redis
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

OTP_EXPIRY_SECONDS = 600  

redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True
)

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def save_otp(user_id: int, otp: str):
    redis_client.setex(f"otp:{user_id}", OTP_EXPIRY_SECONDS, otp)

def verify_otp(user_id: int, otp: str) -> bool:
    stored = redis_client.get(f"otp:{user_id}")
    if stored and stored == otp:
        redis_client.delete(f"otp:{user_id}")
        return True
    return False

def send_otp_email(to_email: str, otp: str, name: str = ""):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    from_email = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user or not smtp_pass:
        print(f"[DEV] OTP for {to_email}: {otp}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your ResearchMind verification code"
    msg["From"] = from_email
    msg["To"] = to_email

    text = f"Your verification code is: {otp}\n\nExpires in 10 minutes."

    html = f"""
    <div style="font-family:sans-serif;max-width:400px;margin:0 auto;padding:24px;">
        <div style="background:#534AB7;width:36px;height:36px;border-radius:8px;
                    display:flex;align-items:center;justify-content:center;margin-bottom:16px;">
            <span style="color:white;font-weight:bold;font-size:16px;">R</span>
        </div>
        <h2 style="color:#111;margin-bottom:8px;">Verify your email</h2>
        <p style="color:#666;margin-bottom:24px;">Hi {name}, enter this code to verify your account:</p>
        <div style="background:#f4f4f4;border-radius:12px;padding:20px;text-align:center;margin-bottom:24px;">
            <span style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#534AB7;">{otp}</span>
        </div>
        <p style="color:#999;font-size:12px;">Expires in 10 minutes. If you didn't request this, ignore this email.</p>
    </div>
    """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
    except Exception as e:
        print(f"Email error: {e}")
        print(f"[DEV] OTP for {to_email}: {otp}")