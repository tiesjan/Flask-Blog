from __future__ import annotations

from typing import TYPE_CHECKING

from flask_blog.blog.models import BlogCategory, BlogPost
from flask_blog.database.core import db
from flask_blog.utils.datetime import local_now

if TYPE_CHECKING:
    from typing import Any


def global_template_context() -> dict[str, Any]:
    """
    Returns global template rendering context for blog Blueprint.
    """

    all_categories = db.session.query(BlogCategory).order_by(BlogCategory.order_index).all()

    latest_posts = (
        db.session.query(BlogPost)
        .filter(BlogPost.published_at <= local_now())
        .order_by(BlogPost.published_at.desc())
        .limit(5)
        .all()
    )

    return {
        "all_categories": all_categories,
        "latest_posts": latest_posts,
    }
