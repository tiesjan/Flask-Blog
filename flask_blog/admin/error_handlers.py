from __future__ import annotations

from typing import TYPE_CHECKING, Union

from flask import flash, g, make_response, redirect, render_template, url_for
from flask_login import login_required  # type: ignore[import]
from werkzeug.exceptions import HTTPException

from flask_blog.admin.decorators import admin_templated
from flask_blog.admin.exceptions import EndpointNotFound

if TYPE_CHECKING:
    from typing import Any

    from flask_blog.admin.decorators import HttpResponse
    from flask_blog.admin.exceptions import DatabaseObjectNotFound


def handle_http_exception(exception: HTTPException) -> HttpResponse:
    """
    Renders `exception` into an HTTP response.

    If the incoming request originates from the HTMX library, a `text/plain` response is returned.
    Otherwise, a `text/html` response is returned.
    """

    if g.htmx_request is True:
        template_name = "admin/exception.txt"
        template_context: dict[str, Any] = {
            "exception": exception,
        }
        mimetype = "text/plain"

    else:
        template_name = "admin/exception.html"
        template_context = {
            "page_title": f"{exception.code or ''} {exception.name}".strip(),
            "exception": exception,
        }
        mimetype = "text/html"

    response = make_response(render_template(template_name, **template_context), exception.code)
    response.mimetype = mimetype

    return response


@admin_templated(template_name="exception.html")
def handle_not_found_exception(
    exception: Union[DatabaseObjectNotFound, EndpointNotFound]
) -> HttpResponse:
    """
    Handles specialized Not Found exceptions.

    The exception's description is flashed to the user after redirecting back to the index.
    """

    flash(exception.description, category="danger")

    return redirect(url_for("admin.web.index"))


@login_required
def handle_unknown_endpoint(endpoint: str) -> HttpResponse:
    """
    Admin view for unhandled endpoint.

    Raises an EndpointNotFound exception. Requires login to prevent endpoint enumeration attacks.
    """

    raise EndpointNotFound(endpoint=endpoint)
