from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Markup, flash, redirect, render_template_string, url_for
from flask_login import (  # type: ignore[import]
    current_user,
    login_required,
    login_user,
    logout_user,
)

from flask_blog.admin.decorators import admin_templated, fetch_object
from flask_blog.admin.file_uploads import detect_file_references
from flask_blog.admin.web.forms import (
    AdminLoginForm,
    BlogCategoryForm,
    BlogPostForm,
    ObjectDeleteForm,
)
from flask_blog.auth import get_next_url
from flask_blog.blog.models import BlogCategory, BlogPost
from flask_blog.database.core import db
from flask_blog.utils.datetime import local_now

if TYPE_CHECKING:
    from typing import Union

    from flask_blog.admin.decorators import HttpResponse, TemplateContext


@admin_templated(template_name="login.html", default_page_title="Login")
def login() -> Union[HttpResponse, TemplateContext]:
    """
    Admin view for login endpoint.

    If the admin user is already logged in or on successful login, the visitor is redirected to the
    validated next URL. On successful login, admin user details are updated too.
    """

    next_url = get_next_url(default_next_url="admin.web.index")

    if current_user.is_authenticated:
        return redirect(next_url)

    form = AdminLoginForm()
    if form.validate_on_submit():
        login_user(form.admin_user, remember=form.remember.data)

        # Update admin user details on successful login
        form.admin_user.last_login_at = local_now()
        if form.admin_user.password_hash_needs_upgrade():
            form.admin_user.set_password_hash(raw_password=form.password.data)
        db.session.commit()

        return redirect(next_url)

    return {"form": form}


def logout() -> HttpResponse:
    """
    Admin view for logout endpoint.

    Afterwards, the visitor is redirected to the login view.
    """

    if current_user.is_authenticated:
        logout_user()

    return redirect(url_for("admin.web.login"))


@login_required
@admin_templated(template_name="index.html", default_page_title="Index")
def index() -> TemplateContext:
    """
    Admin view for index endpoint.
    """

    return {}


@login_required
@admin_templated(template_name="category_list.html", default_page_title="Manage categories")
def blog_category_list() -> TemplateContext:
    """
    Admin view for category list endpoint.
    """

    categories = db.session.query(BlogCategory).order_by(BlogCategory.order_index).all()
    return {"categories": categories}


@login_required
@admin_templated(template_name="category_form.html")
@fetch_object(model=BlogCategory, construct_empty=True)
def blog_category_form(model_object: BlogCategory) -> Union[HttpResponse, TemplateContext]:
    """
    Admin view for category form endpoint.

    If the given `category` has its `id` set, an existing category is edited. If not, a new category
    is created.
    """

    form = BlogCategoryForm(obj=model_object)

    if form.save_changes.data is True and form.validate_on_submit():
        form.populate_obj(model_object)

        db.session.add(model_object)
        db.session.commit()

        # Flash success message
        template = (
            "Successfully {{ performed_action }} category: <strong>{{ category.name }}</strong>. "
            "You can continue editing it below."
        )
        performed_action = "created" if model_object.id is None else "edited"
        message = render_template_string(
            template, performed_action=performed_action, category=model_object
        )
        flash(Markup(message), category="success")

        return redirect(url_for("admin.web.blog_category_form", object_id=model_object.id))

    elif form.cancel_changes.data is True:
        return redirect(url_for("admin.web.blog_category_list"))

    page_title = "Create category" if model_object.id is None else "Edit category"

    return {"form": form, "category": model_object, "page_title": page_title}


@login_required
@admin_templated(template_name="category_delete.html", default_page_title="Delete category")
@fetch_object(model=BlogCategory)
def blog_category_delete(model_object: BlogCategory) -> Union[HttpResponse, TemplateContext]:
    """
    Admin view for category delete endpoint.

    Renders a confirmation form prior to deletion.
    """

    assert model_object.id is not None

    form = ObjectDeleteForm()

    if model_object.associated_blog_post_count == 0:
        if form.confirm_delete.data is True and form.validate_on_submit():
            db.session.delete(model_object)
            db.session.commit()

            # Flash success message
            template = "Successfully deleted category: <strong>{{ category.name }}</strong>. "
            message = render_template_string(template, category=model_object)
            flash(Markup(message), category="success")

            return redirect(url_for("admin.web.blog_category_list"))

        elif form.cancel_delete.data is True:
            return redirect(url_for("admin.web.blog_category_form", object_id=model_object.id))

    return {"form": form, "category": model_object}


@login_required
@admin_templated(template_name="post_list.html", default_page_title="Manage posts")
def blog_post_list() -> TemplateContext:
    """
    Admin view for post list endpoint.
    """

    posts = db.session.query(BlogPost).order_by(BlogPost.title, BlogPost.slug).all()
    return {"posts": posts}


@login_required
@admin_templated(template_name="post_form.html")
@fetch_object(model=BlogPost, construct_empty=True)
def blog_post_form(model_object: BlogPost) -> Union[HttpResponse, TemplateContext]:
    """
    Admin view for post form endpoint.

    If a given `post` has its `id` set, an existing post is edited. If not, a new post is created.
    """

    form = BlogPostForm(obj=model_object)

    categories = (
        db.session.query(BlogCategory.id, BlogCategory.name)
        .order_by(BlogCategory.name, BlogCategory.id)
        .all()
    )
    form.category_id.choices = [(category.id, category.name) for category in categories]

    if form.save_changes.data is True and form.validate_on_submit():
        form.populate_obj(model_object)

        # Link files detected in markdown content
        model_object.files = detect_file_references(markdown_text=form.content.data)

        db.session.add(model_object)
        db.session.commit()

        # Flash success message
        template = (
            "Successfully {{ performed_action }} post: <strong>{{ post.title }}</strong>. "
            "You can continue editing it below."
        )
        performed_action = "created" if model_object.id is None else "edited"
        message = render_template_string(
            template, performed_action=performed_action, post=model_object
        )
        flash(Markup(message), category="success")

        return redirect(url_for("admin.web.blog_post_form", object_id=model_object.id))

    elif form.cancel_changes.data is True:
        return redirect(url_for("admin.web.blog_post_list"))

    page_title = "Create post" if model_object.id is None else "Edit post"

    return {"form": form, "post": model_object, "page_title": page_title}


@login_required
@admin_templated(template_name="post_delete.html", default_page_title="Delete post")
@fetch_object(model=BlogPost)
def blog_post_delete(model_object: BlogPost) -> Union[HttpResponse, TemplateContext]:
    """
    Admin view for post delete endpoint.

    Renders a confirmation form prior to deletion.
    """

    assert model_object.id is not None

    form = ObjectDeleteForm()

    if form.confirm_delete.data is True and form.validate_on_submit():
        db.session.delete(model_object)
        db.session.commit()

        # Flash success message
        template = "Successfully deleted post: <strong>{{ post.title }}</strong>. "
        message = render_template_string(template, post=model_object)
        flash(Markup(message), category="success")

        return redirect(url_for("admin.web.blog_post_list"))

    elif form.cancel_delete.data is True:
        return redirect(url_for("admin.web.blog_post_form", object_id=model_object.id))

    return {"form": form, "post": model_object}
