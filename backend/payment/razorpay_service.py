import razorpay
import hmac
import hashlib
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET
from database.postgres import get_connection

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

PRO_PRICE_INR = 249

def create_order(user_id: int):
    order = client.order.create({
        "amount": PRO_PRICE_INR * 100,  # paise
        "currency": "INR",
        "notes": {"user_id": str(user_id)}
    })
    return order

def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False

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