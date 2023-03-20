from __future__ import annotations

from typing import TYPE_CHECKING

import magic
from wtforms.validators import ValidationError  # type: ignore[import]

if TYPE_CHECKING:
    from typing import Sequence

    from wtforms import FileField, Form  # type: ignore[import]


ALLOWED_IMAGE_EXTENSIONS = (
    "gif",
    "jpeg",
    "jpg",
    "png",
    "webp",
)

ALLOWED_IMAGE_MIMETYPES = (
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
)

ALLOWED_IMAGE_MIMETYPES_DESCRIPTION = (
    "Allowed file types: "
    f"{', '.join([mime.rsplit('/', maxsplit=1)[-1].lower() for mime in ALLOWED_IMAGE_MIMETYPES])}"
)


class MIMETypeAllowed:
    """
    Form validator for validating the MIME type of submitted `FileField` data.

    MIME types are detected using the `libmagic` library.
    """

    def __init__(self, *, allowed_mimetypes: Sequence[str]) -> None:
        self.allowed_mimetypes = allowed_mimetypes

    def __call__(self, form: Form, field: FileField) -> None:
        mimetype = magic.from_descriptor(field.data.stream.fileno(), mime=True)

        if mimetype not in self.allowed_mimetypes:
            raise ValidationError(ALLOWED_IMAGE_MIMETYPES_DESCRIPTION)
