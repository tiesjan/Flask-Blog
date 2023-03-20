from __future__ import annotations

import itertools
import json
import os
from typing import TYPE_CHECKING

from flask import make_response, render_template, request, url_for
from flask_login import login_required  # type: ignore[import]
from werkzeug.exceptions import BadRequest

from flask_blog.admin.api.forms import ImageUploadForm
from flask_blog.admin.decorators import admin_templated, htmx_required
from flask_blog.admin.file_uploads import FileCollection, store_file
from flask_blog.blog.models import BlogCategory
from flask_blog.database.core import db
from flask_blog.text_rendering import LinkTarget, markdown_to_html

if TYPE_CHECKING:
    from typing import Union

    from flask_blog.admin.decorators import HttpResponse, TemplateContext


@login_required
@htmx_required
@admin_templated(template_name="partials/sortable_categories.html")
def order_blog_categories() -> Union[HttpResponse, TemplateContext]:
    """
    Admin API view for ordering blog categories.
    """

    # Validate submitted category IDs
    submitted_category_ids = request.form.getlist("category_id", type=int)
    if len(submitted_category_ids) == 0:
        raise BadRequest("Parameter list `category_id` missing or containing invalid ID values.")

    categories_query = db.session.query(BlogCategory).order_by(BlogCategory.order_index)

    categories = categories_query.with_for_update().populate_existing().all()
    existing_categories_by_id = {category.id: category for category in categories}

    # Abort if the set of submitted categories don't match the existing ones
    if set(submitted_category_ids) != existing_categories_by_id.keys():
        return {"categories": categories}

    # Abort if the ordering of submitted categories is equal to the ordering of the existing ones
    if submitted_category_ids == list(existing_categories_by_id.keys()):
        return {"categories": categories}

    # First set temporary order indexes
    temp_order_index = itertools.count(start=-1, step=-1)
    for category_id in submitted_category_ids:
        category = existing_categories_by_id[category_id]
        category.order_index = next(temp_order_index)

    db.session.flush()

    # Then set new order indexes
    new_order_index = itertools.count(start=1, step=1)
    for category_id in submitted_category_ids:
        category = existing_categories_by_id[category_id]
        category.order_index = next(new_order_index)

    db.session.commit()

    categories = categories_query.all()
    return {"categories": categories}


@login_required
@htmx_required
def render_html() -> HttpResponse:
    """
    Admin API view for rendering Markdown text to HTML.

    Expects form parameter `markdown_text_field` to denote the field containing Markdown text to
    render to HTML, and the Markdown content in a form parameter with that name.
    """

    markdown_text = request.form.get("markdown_text")
    if not markdown_text:
        raise BadRequest("Form parameter `markdown_text` missing.")

    html_text = markdown_to_html(markdown_text=markdown_text, link_target=LinkTarget.BLANK)

    return make_response(html_text)


@login_required
@htmx_required
@admin_templated(template_name="partials/image_uploader.html")
def upload_image() -> Union[HttpResponse, TemplateContext]:
    """
    Admin API view that handles image uploads.

    Once the file is submitted, the file is stored on disk and in the database, and a response with
    the HTMX event `finalizeUpload` is returned. If a GET request comes in, the upload form is
    returned inside a dialog.
    """

    form = ImageUploadForm()

    if form.validate_on_submit():
        file_collection = FileCollection.IMAGES
        file, is_new_file = store_file(file=form.image_file.data, file_collection=file_collection)

        public_url = url_for(
            "serve_media_file", collection=file_collection.value, filename=file.filename
        )
        htmx_event = {
            "finalizeUpload": {
                "file_id": file.id,
                "file_type": "image",
                "file_url": public_url,
                "new_file": is_new_file,
                "metadata": {
                    "alt": os.path.splitext(file.filename)[0],
                },
            }
        }

        template_name = "admin/messages/upload_finalized.html"
        template_context = {"filename": file.filename, "is_new_file": is_new_file}
        response = make_response(render_template(template_name, **template_context))
        response.headers["HX-Trigger"] = json.dumps(htmx_event)

        return response

    return {"form": form, "with_dialog": (request.method == "GET")}
