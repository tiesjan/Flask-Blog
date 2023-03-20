from flask import Blueprint, g, request
from werkzeug.exceptions import HTTPException

from flask_blog.admin import cli, error_handlers
from flask_blog.admin.api.blueprint import api
from flask_blog.admin.exceptions import DatabaseObjectNotFound, EndpointNotFound
from flask_blog.admin.templates import (
    render_admin_form_errors,
    render_admin_form_field,
    render_admin_truthy_icon,
)
from flask_blog.admin.web.blueprint import web

admin = Blueprint(
    "admin",
    __name__,
    cli_group="blog-admin",
    static_folder="static/",
    static_url_path="static/",
    template_folder="templates/",
)

# Nested blueprints
admin.register_blueprint(api, url_prefix="/api/")
admin.register_blueprint(web, url_prefix="/")

# CLI commands
admin.cli.add_command(cli.activate_user)
admin.cli.add_command(cli.create_user)
admin.cli.add_command(cli.deactivate_user)
admin.cli.add_command(cli.delete_user)
admin.cli.add_command(cli.reset_user_password)

# Template helpers
admin.add_app_template_global(render_admin_form_errors)
admin.add_app_template_global(render_admin_form_field)
admin.add_app_template_global(render_admin_truthy_icon)

# Error handlers
admin.register_error_handler(HTTPException, error_handlers.handle_http_exception)
admin.register_error_handler(DatabaseObjectNotFound, error_handlers.handle_not_found_exception)
admin.register_error_handler(EndpointNotFound, error_handlers.handle_not_found_exception)

# Catch all URL rule
admin.add_url_rule(
    "/<path:endpoint>", view_func=error_handlers.handle_unknown_endpoint, methods=["GET", "POST"]
)


# Request pre-processors
@admin.before_request
def detect_htmx_request() -> None:
    """
    Detects whether incoming request originates from the HTMX library and stores the result as
    `g.htmx_request`.

    Checks for the presence and the expected value of the HTTP header `HX-Request`.
    """

    if request.headers.get("HX-Request") == "true":
        g.htmx_request = True

    else:
        g.htmx_request = False
