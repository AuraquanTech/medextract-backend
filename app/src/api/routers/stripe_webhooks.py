from fastapi import APIRouter, Request, HTTPException, Depends
from src.security.webhooks import verify_stripe_signature
from src.infra.config import get_settings

router = APIRouter(prefix="/webhooks", tags=["stripe"])

@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    secret = get_settings().stripe.webhook_secret.get_secret_value()
    if not verify_stripe_signature(payload, sig, secret):
        raise HTTPException(status_code=400, detail="Invalid signature")
    return {"received": True}
