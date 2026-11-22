"""Test helper functions for integration tests"""
import uuid


def get_auth_token(client):
    """
    Helper function to authenticate and get JWT token.
    Returns the access token that can be used in Authorization header.
    """
    # Sign in
    sign_in_response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": "10000000-0000-0000-0000-000000000201"
    })
    
    if sign_in_response.status_code != 200:
        raise Exception(f"Sign-in failed: {sign_in_response.json()}")
    
    session_id = sign_in_response.json()["session_id"]
    
    # Submit proof
    proof_response = client.post(
        "/api/v1/auth/proof",
        json={
            "session_id": session_id,
            "proof_type": "passcode",
            "proof_value": "123456",
            "device_id": "10000000-0000-0000-0000-000000000201"
        }
    )
    
    if proof_response.status_code != 200:
        raise Exception(f"Proof failed: {proof_response.json()}")
    
    return proof_response.json()["access_token"]
