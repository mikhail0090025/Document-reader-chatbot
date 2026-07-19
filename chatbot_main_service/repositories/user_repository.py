from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import User


class UserRepository:
    """
    Repository responsible only for database operations
    related to the User model.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================
    # Create
    # ==========================================================

    def create(
        self,
        *,
        first_name: str,
        last_name: str,
        username: str,
        password_hash: str,
    ) -> User:

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password_hash=password_hash,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    # ==========================================================
    # Read
    # ==========================================================

    def get_by_id(self, user_id: int) -> User | None:

        statement = (
            select(User)
            .where(User.id == user_id)
        )

        return self.db.scalar(statement)

    def get_by_username(self, username: str) -> User | None:

        statement = (
            select(User)
            .where(User.username == username)
        )

        return self.db.scalar(statement)

    def get_all(self) -> list[User]:

        statement = select(User)

        return list(self.db.scalars(statement).all())

    # ==========================================================
    # Update
    # ==========================================================

    def update(
        self,
        user: User,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        password_hash: str | None = None,
    ) -> User:

        if first_name is not None:
            user.first_name = first_name

        if last_name is not None:
            user.last_name = last_name

        if password_hash is not None:
            user.password_hash = password_hash

        self.db.commit()
        self.db.refresh(user)

        return user

    # ==========================================================
    # Delete
    # ==========================================================

    def delete(self, user: User) -> None:

        self.db.delete(user)
        self.db.commit()

    # ==========================================================
    # Utility
    # ==========================================================

    def exists_by_username(self, username: str) -> bool:

        statement = (
            select(User.id)
            .where(User.username == username)
        )

        return self.db.scalar(statement) is not None

    def count(self) -> int:

        return len(self.get_all())