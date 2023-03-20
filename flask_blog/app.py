from __future__ import annotations

import logging
from logging.handlers import WatchedFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

import click
from flask import Flask

from flask_blog.admin.blueprint import admin as admin_blueprint
from flask_blog.auth import login_manager
from flask_blog.blog.blueprint import blog as blog_blueprint
from flask_blog.config.checks import check_app_config
from flask_blog.database.core import db
from flask_blog.templates import format_datetime

if TYPE_CHECKING:
    from flask import Response


def create_app() -> Flask:
    app = Flask(
        __name__,
        # Disable static files and templates on application level
        static_folder=None,
        static_host=None,
        static_url_path=None,
        template_folder=None,
    )

    # Configure application
    app.config.from_object("flask_blog.config.defaults")
    app.config.from_envvar("FLASK_BLOG_CONFIG_FILE", silent=True)
    check_app_config(app_config=app.config)

    # Configure logging if log file is set in app configuration
    if "LOG_FILE" in app.config:
        log_level = logging.INFO if app.debug else logging.WARNING
        logging.basicConfig(
            format=app.config["LOG_FORMAT"],
            level=log_level,
            handlers=[WatchedFileHandler(filename=app.config["LOG_FILE"])],
        )

        for logger_name in ("sqlalchemy", "werkzeug"):
            logging.getLogger(logger_name).setLevel(log_level)

    # Initialize apps
    db.init_app(app)
    login_manager.init_app(app)

    # Register CLI command group
    app.cli.add_command(blog_cli, name="blog")

    # Register template helpers
    app.add_template_filter(format_datetime)

    # Register URL rules
    media_url_prefix = app.config["MEDIA_URL_PREFIX"].rstrip("/")
    serve_media_file_url = f"{media_url_prefix}/<string:collection>/<string:filename>"
    if app.debug:
        app.add_url_rule(serve_media_file_url, view_func=serve_media_file)
    else:
        app.add_url_rule(serve_media_file_url, endpoint=serve_media_file.__name__, build_only=True)

    # Register Admin blueprint
    app.register_blueprint(admin_blueprint, url_prefix="/admin/")

    # Register Blog blueprint
    blog_blueprint.static_folder = app.config["BLOG_STATIC_PATH"]
    blog_blueprint.template_folder = app.config["BLOG_TEMPLATES_PATH"]
    app.register_blueprint(blog_blueprint, url_prefix="/")

    return app


# CLI commands
@click.group()
def blog_cli() -> None:
    pass


@blog_cli.command()
def create_db() -> None:
    """
    Creates tables that do not yet exist in the database.
    """

    click.echo("Creating tables that do not yet exist in the database...")

    db.create_all()


# View functions
def serve_media_file(collection: str, filename: str) -> Response:
    """
    View function to serve a file from the media directory.

    Note: this is only registered in debug mode.
    """

    from flask import current_app, send_from_directory  # pylint: disable=import-outside-toplevel

    collection_media_dir = Path(current_app.config["MEDIA_DIR"]) / collection
    return send_from_directory(collection_media_dir, filename)
