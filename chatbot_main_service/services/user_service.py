from sqlalchemy.orm import Session

from database.models import User
from repositories.user_repository import UserRepository
from schemas.user import (
    UserResponse,
    UpdateUserRequest,
)


class UserService:

    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def get_me(
        self,
        current_user: User
    ) -> UserResponse:

        return UserResponse.model_validate(current_user)

    def update_me(
        self,
        current_user: User,
        request: UpdateUserRequest,
    ) -> UserResponse:

        user = self.users.update(
            current_user,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        self.db.commit()

        self.db.refresh(user)

        return UserResponse.model_validate(user)