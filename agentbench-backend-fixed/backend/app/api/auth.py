from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Generic message on failed login - never reveal whether the email exists,
# that's an account-enumeration vector.
INVALID_CREDENTIALS = "Invalid email or password"


@router.post("/register", response_model=Token)
@limiter.limit("10/minute")
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(new_user.id)

    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    # Deliberately identical error/status for "no such user" and "wrong
    # password" so a caller can't use this endpoint to enumerate accounts.
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)

    token = create_access_token(user.id)

    return {"access_token": token, "token_type": "bearer"}
