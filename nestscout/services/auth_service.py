"""Auth service — registration, login, JWT token management."""

import bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy import select

from nestscout.extensions import db
from nestscout.models.user import User


class AuthService:
    """Handles user authentication and token management."""

    @staticmethod
    def register(username: str, email: str, password: str, role: str = "user") -> User:
        """Register a new user.

        Raises:
            ValueError: If username or email already taken.
        """
        # Check uniqueness
        existing = db.session.execute(
            select(User).where((User.email == email) | (User.username == username))
        ).scalar_one_or_none()

        if existing:
            if existing.email == email:
                raise ValueError("Email already registered")
            raise ValueError("Username already taken")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def login(email: str, password: str) -> dict:
        """Authenticate and return JWT tokens.

        Returns:
            Dict with access_token, refresh_token, and user info.

        Raises:
            ValueError: If credentials are invalid.
        """
        user = db.session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role, "username": user.username},
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }

    @staticmethod
    def get_user_by_id(user_id: int) -> User | None:
        return db.session.get(User, user_id)

    @staticmethod
    def list_users() -> list[User]:
        return list(db.session.execute(select(User).order_by(User.id)).scalars())
