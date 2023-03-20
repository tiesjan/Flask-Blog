from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, MetaData
from sqlalchemy.orm import DeclarativeMeta, declarative_base
from sqlalchemy.sql.schema import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    UniqueConstraint,
)

from flask_blog.database.fields import TZDateTime
from flask_blog.database.functions import from_column
from flask_blog.utils.datetime import local_now

naming_convention = {
    PrimaryKeyConstraint: "pk_%(table_name)s",
    ForeignKeyConstraint: "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    CheckConstraint: "ck_%(table_name)s_%(constraint_name)s",
    UniqueConstraint: "uq_%(table_name)s_%(column_0_N_name)s",
    Index: "ix_%(column_0_N_label)s",
}

metadata = MetaData(naming_convention=naming_convention)  # type: ignore[arg-type]


db = SQLAlchemy(model_class=declarative_base(metadata=metadata, metaclass=DeclarativeMeta))


class BaseModel(db.Model):  # type: ignore[name-defined]
    """
    Abstract base model class.

    Includes a big integer model field `id` that defaults as primary key.
    """

    __abstract__ = True

    id = db.Column(
        db.BigInteger().with_variant(Integer, "sqlite"),
        name="id",
        nullable=False,
        primary_key=True,
    )


class TimestampMixin:
    """
    Model mixin for adding self-updating model fields `created_at` and `updated_at` timestamps.
    """

    created_at = db.Column(
        TZDateTime,
        name="created_at",
        nullable=False,
        default=local_now,
    )

    updated_at = db.Column(
        TZDateTime,
        name="updated_at",
        nullable=False,
        default=from_column(created_at),
        onupdate=local_now,
    )
