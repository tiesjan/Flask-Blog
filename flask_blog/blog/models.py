from __future__ import annotations

from typing import TYPE_CHECKING

from markupsafe import Markup
from sqlalchemy import ColumnDefault, func, select, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression
from werkzeug.utils import cached_property

from flask_blog.database.core import BaseModel, TimestampMixin, db
from flask_blog.database.fields import TZDateTime
from flask_blog.text_rendering import markdown_to_html
from flask_blog.utils.datetime import local_now

if TYPE_CHECKING:
    from sqlalchemy import Table


class BlogCategory(TimestampMixin, BaseModel):
    __tablename__ = "blog_category"

    slug = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, unique=True)

    # Define default for `order_index` separately, so that SQL function can refer to defined column
    order_index.default = ColumnDefault(
        # pylint: disable=not-callable
        select(func.coalesce(func.max(order_index), text("0")) + text("1")).scalar_subquery()
        # pylint: enable=not-callable
    )

    blog_posts = relationship(lambda: BlogPost, back_populates="category")

    @cached_property
    def associated_blog_post_count(self) -> int:
        count: int = (
            db.session.query(func.count(BlogPost.id))  # pylint: disable=not-callable
            .filter(BlogPost.category_id == self.id)
            .scalar()
        )
        return count

    def __repr__(self) -> str:
        return f"<Blog Category {self.name!r}>"


class BlogPost(TimestampMixin, BaseModel):
    __tablename__ = "blog_post"

    category_id = db.Column(
        db.BigInteger, db.ForeignKey(BlogCategory.id, ondelete="RESTRICT"), nullable=False
    )
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    tagline = db.Column(db.String(100), nullable=False)
    header_image_file_id = db.Column(
        db.BigInteger, db.ForeignKey("file.id", ondelete="SET NULL"), nullable=False
    )
    published_at = db.Column(TZDateTime, nullable=True, default=expression.null())
    featured = db.Column(db.Boolean, nullable=False, default=expression.false())

    category = relationship(
        BlogCategory, back_populates="blog_posts", lazy="joined", innerjoin=True
    )
    header_image_file = relationship(lambda: File, foreign_keys=[header_image_file_id])
    files = relationship(
        lambda: File,
        secondary=lambda: blog_post_x_file,
        back_populates="blog_posts",
        passive_deletes=True,
    )

    @property
    def published(self) -> bool:
        """
        Returns whether the blog post is published, based on the `published_at` field.
        """

        return self.published_at is not None

    @published.setter
    def published(self, value: bool) -> None:
        """
        Setter for the `published` property.

        If the given `value` is True, the `published_at` field is updated with the current
        timestamp if not set. The field is cleared otherwise.
        """

        if value is True and self.published_at is None:
            self.published_at = local_now()

        elif value is False and self.published_at is not None:
            self.published_at = None

    @property
    def rendered_content(self) -> str:
        return Markup(markdown_to_html(markdown_text=self.content))

    def __repr__(self) -> str:
        return f"<Blog Post {self.title!r}>"


class File(TimestampMixin, BaseModel):
    __tablename__ = "file"

    MAX_FILENAME_LENGTH = 200

    filename = db.Column(db.String(MAX_FILENAME_LENGTH), nullable=False, unique=True)
    collection = db.Column(db.String(50), nullable=False)
    mimetype = db.Column(db.String(50), nullable=False)
    content_size = db.Column(db.BigInteger, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)

    blog_posts = relationship(
        BlogPost, secondary=lambda: blog_post_x_file, back_populates="files", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<File {self.filename!r}>"


blog_post_x_file: Table = db.Table(
    "blog_post_x_file",
    BaseModel.metadata,
    db.Column("blog_post_id", db.ForeignKey(BlogPost.id, ondelete="CASCADE"), primary_key=True),
    db.Column("file_id", db.ForeignKey(File.id, ondelete="CASCADE"), primary_key=True),
)
