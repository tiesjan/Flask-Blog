from __future__ import annotations

from typing import TYPE_CHECKING

from markupsafe import Markup

if TYPE_CHECKING:
    from datetime import datetime


def format_datetime(value: datetime, datetime_format: str = "%d %b %Y, %H:%M") -> Markup:
    """
    Template filter that converts the given datetime value into a string in the specified format.
    """

    return Markup(value.strftime(datetime_format))
