# app/dependencies.py

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.session import SessionLocal
from repositories.user_repository import UserRepository
from security.jwt import decode_access_token
from services.auth_service import AuthService
from services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ============================================================
# Database
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    Creates a SQLAlchemy session for a single request.
    The session is automatically closed after the request ends.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# Repositories
# ============================================================

def get_user_repository(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


# ============================================================
# Services
# ============================================================

def get_auth_service(
    db: Session = Depends(get_db),
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(db, repository)

def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)


# ============================================================
# Authentication
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    repository: UserRepository = Depends(get_user_repository),
):
    """
    Returns the currently authenticated user.

    Raises:
        HTTPException(401) if the token is invalid or
        the user does not exist.
    """

    payload = decode_access_token(token)

    username = payload.get("sub")

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )

    user = repository.get_by_username(username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user