from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from flask import request, url_for
from flask_login import LoginManager  # type: ignore[import]

from flask_blog.admin.models import AdminUser
from flask_blog.utils.url import is_hosted_url

if TYPE_CHECKING:
    from typing import Optional

SAFE_HTTP_SCHEMES = ("http", "https")

login_manager = LoginManager()
login_manager.blueprint_login_views = {
    # Redirect for `admin` and `admin.web`; return HTTP 401 Unauthorized for `admin.api`
    "admin": "admin.web.login",
    "admin.web": "admin.web.login",
}
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id: str) -> Optional[AdminUser]:
    """
    Loads user from an existing login session.

    When the incoming request is handled by a view function of the Admin blueprint, attempts to
    retrieve an active admin user from the database using its `public_id`.
    """

    if request.blueprint in {"admin", "admin.api", "admin.web"}:
        return AdminUser.get_by_public_id(public_id=user_id)

    return None


def is_safe_url(*, target_url: str) -> bool:
    """
    Determines whether the given target URL is safe to redirect to.

    The target URL should be hosted by this server and the specified `scheme` should be one of the
    predefined safe HTTP schemes.
    """

    split_target_url = urlsplit(target_url, scheme=SAFE_HTTP_SCHEMES[0])

    return bool(is_hosted_url(url=target_url) and split_target_url.scheme in SAFE_HTTP_SCHEMES)


def get_next_url(*, default_next_url: str) -> str:
    """
    Returns the `next` URL from the request args if determined safe, or fall back to the given
    `default_next_url`.
    """

    next_url = request.args.get("next")
    if not next_url or not is_safe_url(target_url=next_url):
        next_url = url_for(default_next_url)
    return next_url
