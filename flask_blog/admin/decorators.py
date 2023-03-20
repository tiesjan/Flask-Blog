from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Mapping, Protocol, Union

import flask
import werkzeug
from flask import g, make_response, render_template
from werkzeug.exceptions import Forbidden

from flask_blog.admin.exceptions import DatabaseObjectNotFound
from flask_blog.database.core import db

if TYPE_CHECKING:
    from typing import Callable, Optional, Type

    from flask_blog.database.core import BaseModel

# Type variables for annotating return types of view functions
HttpResponse = Union[flask.Response, werkzeug.Response]
TemplateContext = Mapping[str, Any]


class ViewFunction(Protocol):
    """
    This protocol represents a view function that takes (keyword) arguments and returns either
    an `HttpResponse` object or a `TemplateContext` object.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> Union[HttpResponse, TemplateContext]:
        ...


def admin_templated(
    *, template_name: str, default_page_title: Optional[str] = None
) -> Callable[[ViewFunction], ViewFunction]:
    """
    View decorator for handling a response or a template context returned by admin view functions.

    A response object is returned as-is; a mapping is used as template context when rendering the
    template with given `template_name`. The optional `default_page_title` is used as fallback for
    the `page_title` context variable.
    """

    def decorator(function: ViewFunction) -> ViewFunction:
        @wraps(function)
        def wrapped_function(*args: Any, **kwargs: Any) -> HttpResponse:
            result = function(*args, **kwargs)

            if isinstance(result, (flask.Response, werkzeug.Response)):
                return result

            elif isinstance(result, Mapping):
                template_context = {
                    "page_title": default_page_title,
                    **result,
                }

                return make_response(render_template(f"admin/{template_name}", **template_context))

            else:
                raise ValueError(f"Invalid result type: {type(result)}.")

        return wrapped_function

    return decorator


def fetch_object(
    *, model: Type[BaseModel], construct_empty: bool = False
) -> Callable[[ViewFunction], ViewFunction]:
    """
    View decorator to fetch an object from the database for the given model type.

    Retrieves the variable part `<int:object_id>` from the URL rule and uses it to query the object
    from the database table that corresponds to the given model type. If the model object is found,
    it is passed to the view as keyword argument `model_object`. If not, a `DatabaseObjectNotFound`
    exception is raised instead.

    If no `object_id` value is provided by the URL rule and `construct_empty` is set to True, the
    view will be given an empty model object. This is useful when handling creates and updates of
    model objects with the same view function:

        @app.route("/user/create/", methods=["GET", "POST"])
        @app.route("/user/<int:object_id>/", methods=["GET", "POST"])
        def user(model_object):
            if model_object.id is None:
                # Create logic
            else:
                # Update logic

    Not specifying the `object_id` in the URL rule and setting `construct_empty` to False will raise
    a `RuntimeError`, as this would result in undefined behavior.
    """

    def decorator(function: ViewFunction) -> ViewFunction:
        @wraps(function)
        def wrapped_function(*args: Any, **kwargs: Any) -> Union[HttpResponse, TemplateContext]:
            # Attempt to fetch model object from database
            object_id = kwargs.pop("object_id", None)
            if object_id is not None:
                model_object = db.session.get(model, object_id)

                if model_object is None:
                    raise DatabaseObjectNotFound(model=model, object_id=object_id)

            # Construct an empty model object if configured
            elif construct_empty is True:
                model_object = model()

            # Raise exception for undefined behavior
            else:
                raise RuntimeError(
                    "No object ID value was provided and not configured to construct an empty "
                    "object. Did you forget to set `@fetch_object(..., construct_empty=True)` "
                    "for this view?"
                )

            kwargs["model_object"] = model_object

            return function(*args, **kwargs)

        return wrapped_function

    return decorator


def htmx_required(function: ViewFunction) -> ViewFunction:
    """
    View decorator for requiring incoming requests to originate from the HTMX library.

    Returns an HTTP 403 Forbidden response for incoming request does not meet requirements.
    """

    @wraps(function)
    def check_htmx(*args: Any, **kwargs: Any) -> Union[HttpResponse, TemplateContext]:
        if g.htmx_request is False:
            raise Forbidden("This endpoint may only be accessed from HTMX.")

        return function(*args, **kwargs)

    return check_htmx
