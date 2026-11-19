"""Idempotency helpers for preventing duplicate operations."""
import hashlib


def generate_idempotency_key(*args) -> str:
    """Generate an idempotency key from input arguments."""
    data = ":".join(str(arg) for arg in args)
    return hashlib.sha256(data.encode()).hexdigest()
