from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.dependencies import get_db
from app.models.user import User

security = HTTPBearer()

def get_current_user(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id = int(payload["sub"])

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user