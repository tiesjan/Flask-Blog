from __future__ import annotations

import hashlib
import secrets
from typing import TYPE_CHECKING

from flask import current_app
from flask_login import UserMixin  # type: ignore[import]
from sqlalchemy.sql import expression
from werkzeug.security import generate_password_hash

from flask_blog.database.core import BaseModel, TimestampMixin, db
from flask_blog.database.fields import TZDateTime

if TYPE_CHECKING:
    from typing import Optional


class AdminUser(UserMixin, TimestampMixin, BaseModel):
    __tablename__ = "admin_user"

    public_id = db.Column(db.String(100), nullable=False, unique=True)
    email_address = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    active = db.Column(db.Boolean, nullable=False, server_default=expression.true())
    last_login = db.Column(TZDateTime, nullable=True, server_default=expression.null())

    @classmethod
    def get_by_email_address(cls, *, email_address: str) -> Optional[AdminUser]:
        """
        Returns first admin user found with the given email address, or None if not present.
        """

        admin_user: Optional[AdminUser] = (
            db.session.query(AdminUser).filter(cls.email_address == email_address).first()
        )
        return admin_user

    @classmethod
    def get_by_public_id(cls, *, public_id: str) -> Optional[AdminUser]:
        """
        Returns first active admin user found with the given public ID, or None if not present.
        """

        admin_user: Optional[AdminUser] = (
            db.session.query(AdminUser)
            .filter(cls.active.is_(True), cls.public_id == public_id)
            .first()
        )
        return admin_user

    @property
    def is_active(self) -> bool:
        """
        Returns whether the AdminUser instance is marked active.

        Overridden from `UserMixin`.
        """

        return self.active is True

    def get_id(self) -> str:
        """
        Returns `public_id` of the AdminUser instance.

        Overridden from `UserMixin`.
        """

        return str(self.public_id)

    def rotate_public_id(self) -> None:
        """
        Rotates the `public_id` of the AdminUser instance.
        """

        hash_value = hashlib.sha256()
        hash_value.update(self.email_address.encode("utf-8"))
        hash_value.update(secrets.token_bytes(64))
        self.public_id = hash_value.hexdigest()

    def set_password_hash(self, *, raw_password: str) -> None:
        """
        Hashes the given `raw_password` and stores the resulting hash on the AdminUser instance.
        """

        hasher = current_app.config["AUTH_PBKDF2_HASHER"]
        iterations = current_app.config["AUTH_PBKDF2_ITERATIONS"]
        method = f"pbkdf2:{hasher}:{iterations}"
        salt_length = current_app.config["AUTH_PBKDF2_SALT_LENGTH"]

        self.password_hash = generate_password_hash(raw_password, method, salt_length)

    def password_hash_needs_upgrade(self) -> bool:
        """
        Determines whether the password hash on the AdminUser instance requires an upgrade based on
        the PBKDF2 configuration.
        """

        if self.password_hash.count("$") != 2:
            raise ValueError("Invalid password hash format.")

        method, salt, _ = self.password_hash.split("$")

        if not method.startswith("pbkdf2:") or method.count(":") != 2:
            raise ValueError("Invalid format for PBKDF2 configuration.")

        _, hasher, iterations = method.split(":")

        return bool(
            hasher != current_app.config["AUTH_PBKDF2_HASHER"]
            or int(iterations) != current_app.config["AUTH_PBKDF2_ITERATIONS"]
            or len(salt) != current_app.config["AUTH_PBKDF2_SALT_LENGTH"]
        )

    def __repr__(self) -> str:
        return f"<Admin User {self.email_address!r}>"
