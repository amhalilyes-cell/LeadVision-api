import os
from fastapi import HTTPException

def require_api_key(x_api_key: str | None):
    token = os.getenv("API_AUTH_TOKEN")
    if not token:
        raise HTTPException(500, "API_AUTH_TOKEN is not set in environment")

    if not x_api_key or x_api_key != token:
        raise HTTPException(401, "Invalid or missing API key")