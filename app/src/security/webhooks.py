import hmac, hashlib
def verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    try:
        signed = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signed, sig_header)
    except Exception:
        return False
