from flask import render_template
from sqlalchemy.sql import expression
from werkzeug.exceptions import NotFound

from flask_blog.blog.models import BlogCategory, BlogPost
from flask_blog.database.core import db
from flask_blog.utils.datetime import local_now


def index() -> str:
    public_posts_query = (
        db.session.query(BlogPost)
        .filter(BlogPost.published_at <= local_now())
        .order_by(BlogPost.published_at.desc())
    )

    featured_posts = (
        public_posts_query.filter(BlogPost.featured == expression.true()).limit(5).all()
    )

    categories = db.session.query(BlogCategory).order_by(BlogCategory.order_index).all()
    posts_by_category = {}
    for category_obj in categories:
        posts = public_posts_query.filter(BlogPost.category_id == category_obj.id).limit(4).all()
        if len(posts):
            posts_by_category[category_obj] = posts

    template_context = {
        "featured_posts": featured_posts,
        "posts_by_category": posts_by_category,
    }
    return render_template("index.html", **template_context)


def category(category_slug: str) -> str:
    category_obj = db.session.query(BlogCategory).filter(BlogCategory.slug == category_slug).first()

    if category_obj is None:
        raise NotFound()

    category_posts = (
        db.session.query(BlogPost)
        .filter(
            BlogPost.published_at <= local_now(),
            BlogPost.category.has(slug=category_slug),
        )
        .order_by(BlogPost.published_at.desc())
        .all()
    )

    template_context = {
        "page_title": category_obj.name,
        "category": category_obj,
        "category_posts": category_posts,
    }
    return render_template("category.html", **template_context)


def post(category_slug: str, post_slug: str) -> str:
    post_obj = (
        db.session.query(BlogPost)
        .filter(
            BlogPost.published_at <= local_now(),
            BlogPost.slug == post_slug,
            BlogPost.category.has(slug=category_slug),
        )
        .first()
    )

    if post_obj is None:
        raise NotFound()

    template_context = {
        "page_title": post_obj.title,
        "post": post_obj,
    }
    return render_template("post.html", **template_context)
