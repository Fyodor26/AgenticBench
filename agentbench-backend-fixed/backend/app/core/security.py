import base64
import hashlib
from datetime import datetime, timedelta, UTC
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError(
            "Password must be 72 bytes or fewer for bcrypt."
        )

    return pwd_context.hash(password)
def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    if len(plain_password.encode("utf-8")) > 72:
        return False

    return pwd_context.verify(
        plain_password,
        hashed_password,
    )
def create_access_token(user_id: int):

    expire = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def _get_fernet() -> Fernet:
    """
    Build the Fernet cipher used to encrypt provider API keys / endpoints
    before they're persisted (agents.api_key, user_settings.*_api_key).

    Uses settings.CREDENTIAL_ENCRYPTION_KEY if provided (recommended for
    every real deployment). If it's not set, a key is deterministically
    derived from SECRET_KEY so the app still runs out of the box in
    development - this is NOT a substitute for setting a dedicated key in
    production, since it means rotating SECRET_KEY also invalidates every
    stored credential.
    """
    raw_key = settings.CREDENTIAL_ENCRYPTION_KEY
    if raw_key:
        return Fernet(raw_key.encode("utf-8"))

    derived = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def encrypt_secret(value: Optional[str]) -> Optional[str]:
    """Encrypt a secret (API key, credential) for storage. Passes through None."""
    if value is None or value == "":
        return None
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: Optional[str]) -> Optional[str]:
    """Decrypt a value previously produced by encrypt_secret. Passes through None."""
    if value is None or value == "":
        return None
    try:
        return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Value wasn't encrypted with the current key (e.g. legacy plaintext
        # row from before this feature existed, or the key was rotated).
        # Fail safe rather than raising into request handlers.
        return None