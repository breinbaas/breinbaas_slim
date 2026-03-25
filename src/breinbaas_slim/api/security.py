from fastapi.security import APIKeyHeader
from fastapi import Depends, HTTPException, status
import secrets
from dotenv import load_dotenv
import os
import json

load_dotenv()


raw_keys = os.getenv("VALID_API_KEYS", "{}")
try:
    VALID_API_KEYS = json.loads(raw_keys)
except json.JSONDecodeError:
    # Failsafe in case the .env formatting is broken
    print("CRITICAL WARNING: VALID_API_KEYS in .env is not valid JSON!")
    VALID_API_KEYS = {}

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_current_client(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
        )

    for valid_key, client_name in VALID_API_KEYS.items():
        if secrets.compare_digest(api_key, valid_key):
            return client_name

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )
