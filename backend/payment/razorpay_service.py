import requests
import hmac
import hashlib
import base64
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET
from database.postgres import get_connection

PRO_PRICE_INR = 249
RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"

def _auth_header():
    credentials = f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def create_order(user_id: int):
    response = requests.post(
        f"{RAZORPAY_BASE_URL}/orders",
        json={
            "amount": PRO_PRICE_INR * 100,
            "currency": "INR",
            "notes": {"user_id": str(user_id)}
        },
        headers=_auth_header()
    )
    response.raise_for_status()
    return response.json()

def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    body = f"{order_id}|{payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def verify_webhook_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def upgrade_user_to_pro(user_id: int, payment_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET plan = 'pro' WHERE id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()