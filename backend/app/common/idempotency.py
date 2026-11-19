"""Idempotency helpers for preventing duplicate operations."""
import hashlib
import uuid


def generate_idempotency_key(*args) -> str:
    """Generate an idempotency key from input arguments."""
    # If no args provided, generate a unique key using UUID
    if not args:
        return str(uuid.uuid4())
    
    data = ":".join(str(arg) for arg in args)
    return hashlib.sha256(data.encode()).hexdigest()
