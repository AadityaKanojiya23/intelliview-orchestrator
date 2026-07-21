import hashlib

def generate_idempotency_key(event, user):
    data = f"{event}:{user}"
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()