from fastapi import APIRouter, Request, Response, Depends, HTTPException
from pydantic import BaseModel
from auth.jwt import get_current_user
from payment.razorpay_service import (
    create_order, verify_payment_signature,
    verify_webhook_signature, upgrade_user_to_pro
)
import json

router = APIRouter(prefix="/payment", tags=["payment"])

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@router.post("/create-order", dependencies=[Depends(get_current_user)])
def create_payment_order(request: Request, response: Response):
    user_id = get_current_user(request, response)
    order = create_order(user_id)
    return {"order_id": order["id"], "amount": order["amount"], "currency": order["currency"]}

@router.post("/verify", dependencies=[Depends(get_current_user)])
def verify_payment(data: VerifyPaymentRequest, request: Request, response: Response):
    user_id = get_current_user(request, response)

    valid = verify_payment_signature(
        data.razorpay_order_id,
        data.razorpay_payment_id,
        data.razorpay_signature
    )
    if not valid:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    upgrade_user_to_pro(user_id, data.razorpay_payment_id)
    return {"status": "success", "plan": "pro"}

@router.post("/webhook")
async def razorpay_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = json.loads(body)
    event = payload.get("event")

    if event == "payment.captured":
        payment_entity = payload["payload"]["payment"]["entity"]
        user_id = int(payment_entity["notes"]["user_id"])
        upgrade_user_to_pro(user_id, payment_entity["id"])

    return {"status": "ok"}