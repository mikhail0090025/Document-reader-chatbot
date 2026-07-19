from sqlalchemy.orm import Session

from database.models import Chat
from repositories.user_repository import UserRepository
from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
)
from security.password import (
    hash_password,
    verify_password,
)
from security.jwt import create_access_token


class AuthService:

    def __init__(
        self,
        db: Session,
        users: UserRepository,
    ):
        self.db = db
        self.users = users

    def register(self, request: RegisterRequest) -> AuthResponse:

        if self.users.exists_by_username(request.username):
            raise ValueError("Username already exists.")

        password_hash = hash_password(request.password)

        user = self.users.create(
            first_name=request.first_name,
            last_name=request.last_name,
            username=request.username,
            password_hash=password_hash,
        )

        chat = Chat(user_id=user.id)

        self.db.add(chat)

        self.db.commit()

        token = create_access_token(user.id)

        return AuthResponse(
            access_token=token
        )

    def login(self, request: LoginRequest) -> AuthResponse:

        user = self.users.get_by_username(request.username)

        if user is None:
            raise ValueError("Invalid username or password.")

        if not verify_password(
            request.password,
            user.password_hash
        ):
            raise ValueError("Invalid username or password.")

        token = create_access_token(user.id)

        return AuthResponse(
            access_token=token
        )

    def delete_account(self, current_user):

        self.users.delete(current_user)

        self.db.commit()