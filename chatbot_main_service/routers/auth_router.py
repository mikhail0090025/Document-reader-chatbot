from fastapi import APIRouter, Depends, HTTPException, status

from schemas.auth import LoginRequest, TokenResponse
from services.auth_service import AuthService
from dependencies import get_auth_service

from schemas.user import (
    UpdateUserRequest,
    UserResponse
)

from schemas.auth import RegisterRequest

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.register(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    token = auth_service.login(request)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    return TokenResponse(access_token=token)