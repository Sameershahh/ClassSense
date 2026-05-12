# backend/auth.py
# JWT-based authentication.
# Provides: login endpoint, token creation, get_current_user dependency.

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from dotenv import load_dotenv

from backend.models.schemas import Token, TokenData

load_dotenv()

# ── Configuration ────────────────────────────────────────────
SECRET_KEY  = os.getenv("SECRET_KEY", "classsense-change-this-in-production-min32chars!")
ALGORITHM   = "HS256"
EXPIRE_MINS = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours

# ── Crypto ───────────────────────────────────────────────────
pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ── Hardcoded users for MVP ───────────────────────────────────
# Replace with a DB-backed user table in production.
USERS_DB: dict = {
    "instructor@classsense.com": {
        "hashed_password": pwd_context.hash("instructor123"),
        "role": "instructor",
        "full_name": "ClassSense Instructor",
    },
    "admin@classsense.com": {
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
        "full_name": "ClassSense Admin",
    },
}

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_user(username: str) -> Optional[dict]:
    return USERS_DB.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire  = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=EXPIRE_MINS)
    )
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── Dependency: get current authenticated user ────────────────

def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    FastAPI dependency. Decodes the JWT and returns the token payload.
    Raises HTTP 401 if the token is invalid or expired.

    Usage in any protected endpoint:
        @router.get("/protected")
        def protected(user: TokenData = Depends(get_current_user)):
            ...
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str     = payload.get("role", "instructor")
        if username is None:
            raise credentials_exc
        return TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exc


def require_admin(user: TokenData = Depends(get_current_user)) -> TokenData:
    """Dependency that only allows admin-role users."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# ── Login endpoint ────────────────────────────────────────────

@router.post("/token", response_model=Token, summary="Login and get JWT token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    Standard OAuth2 password flow.
    Returns a Bearer JWT valid for 8 hours (one teaching day).

    **Default credentials (change in production):**
    - instructor@classsense.com / instructor123
    - admin@classsense.com / admin123
    """
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": form.username, "role": user["role"]},
        expires_delta=timedelta(minutes=EXPIRE_MINS),
    )
    return Token(access_token=token, token_type="bearer")


@router.get("/me", summary="Get current user info")
def get_me(user: TokenData = Depends(get_current_user)):
    """Returns info about the currently authenticated user."""
    db_user = get_user(user.username)
    return {
        "username" : user.username,
        "role"     : user.role,
        "full_name": db_user.get("full_name") if db_user else None,
    }
