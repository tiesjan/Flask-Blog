from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def lower(value: Any) -> Any:
    """
    Converts the value to lowercase, if the value type supports it.
    """

    if hasattr(value, "lower"):
        value = value.lower()

    return value


def strip_value(value: Any) -> Any:
    """
    Strips whitespace characters surrounding the value, if the value type supports it.
    """

    if hasattr(value, "strip"):
        value = value.strip()

    return value
