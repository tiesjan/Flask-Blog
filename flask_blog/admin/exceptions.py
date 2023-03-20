from __future__ import annotations

from typing import TYPE_CHECKING

from werkzeug.exceptions import NotFound

if TYPE_CHECKING:
    from typing import Any, Type

    from flask_blog.database.core import BaseModel


class DatabaseObjectNotFound(NotFound):
    """
    Error to signal that the requested database object was not found.
    """

    def __init__(self, *, model: Type[BaseModel], object_id: Any):
        self.description = (
            f"Unable to find {model.__name__} with ID {object_id}. Perhaps it was deleted?"
        )

        super().__init__()


class EndpointNotFound(NotFound):
    """
    Error to signal that the requested endpoint was not found.
    """

    description = "That page does not seem to exist."

    def __init__(self, *, endpoint: str):
        self.endpoint = endpoint

        super().__init__()
