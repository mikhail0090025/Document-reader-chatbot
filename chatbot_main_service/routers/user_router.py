from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status
)

from schemas.user import (
    UpdateUserRequest,
    UserResponse
)

from services.user_service import UserService
from dependencies import (
    get_current_user,
    get_user_service
)

from database.models import User

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse
)
def update_me(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return service.update_user(
        current_user.id,
        request
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_me(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    service.delete_user(current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)