from __future__ import annotations

from typing import TYPE_CHECKING

from flask import make_response, render_template

if TYPE_CHECKING:
    from flask import Response
    from werkzeug.exceptions import HTTPException


def handle_http_exception(exception: HTTPException) -> Response:
    """
    Renders `exception` into an HTTP response.
    """

    template_context = {
        "page_title": f"{exception.code or ''} {exception.name}".strip(),
        "exception": exception,
    }

    return make_response(render_template("exception.html", **template_context), exception.code)
