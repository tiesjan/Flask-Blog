from flask import Blueprint, abort
from werkzeug.exceptions import HTTPException

from flask_blog.blog import error_handlers, views
from flask_blog.blog.templates import global_template_context

blog = Blueprint(
    "blog",
    __name__,
    static_url_path="static/",
)

# URL rules
blog.add_url_rule("/", view_func=views.index, methods=["GET"])
blog.add_url_rule("/<string:category_slug>/", view_func=views.category, methods=["GET"])
blog.add_url_rule(
    "/<string:category_slug>/<string:post_slug>/", view_func=views.post, methods=["GET"]
)

# Template helpers
blog.context_processor(global_template_context)

# Error handlers
blog.register_error_handler(HTTPException, error_handlers.handle_http_exception)

# Catch all URL rule: abort with HTTP 404 Not Found
blog.add_url_rule(
    "/<path:endpoint>", view_func=lambda endpoint: abort(404), methods=["GET", "POST"]
)
