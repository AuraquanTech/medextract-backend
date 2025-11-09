import hashlib, json
def sha256_hex(obj) -> str:
    if isinstance(obj, (dict, list)):
        payload = json.dumps(obj, sort_keys=True).encode()
    elif isinstance(obj, (bytes, bytearray)):
        payload = obj
    else:
        payload = str(obj).encode()
    return hashlib.sha256(payload).hexdigest()
