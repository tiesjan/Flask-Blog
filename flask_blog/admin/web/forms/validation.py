from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sqlalchemy import select
from wtforms.validators import ValidationError  # type: ignore[import]

from flask_blog.blog.models import File
from flask_blog.database.core import db

if TYPE_CHECKING:
    from typing import Optional

    from wtforms import Form, IntegerField, StringField  # type: ignore[import]

    from flask_blog.admin.file_uploads import FileCollection


SLUG_DESCRIPTION = "Enter letters, numbers, underscores and hyphens only."

SLUG_RESERVED_VALUES = {
    "admin",
    "search",
    "static",
}


class FileExists:
    """
    Form validator for validating whether the File with the provided ID exists.

    The files to check can optionally be filtered by the given FileCollection.
    """

    def __init__(self, *, file_collection: Optional[FileCollection] = None):
        self.file_collection = file_collection

    def __call__(self, form: Form, field: IntegerField) -> None:
        if field.data is not None:
            filter_clause = File.id == field.data
            if self.file_collection is not None:
                filter_clause &= File.collection == self.file_collection.value

            file_exists_query = select(File.id).filter(filter_clause).exists()

            image_file_exists: bool = db.session.query(file_exists_query).scalar()

            if image_file_exists is False:
                raise ValidationError("This image file does not exist.")


class Slug:
    """
    Form validator for validating whether the slug value is valid and not reserved.

    A pattern can optionally be specified for the slug regex. The regex is matched case-insensitive.
    """

    def __init__(self, *, slug_regex_pattern: str = r"^[a-z0-9-_]+$"):
        self.slug_regex = re.compile(slug_regex_pattern, flags=re.IGNORECASE)

    def __call__(self, form: Form, field: StringField) -> None:
        if field.data is not None:
            if self.slug_regex.match(field.data) is None:
                raise ValidationError(SLUG_DESCRIPTION)

            if field.data in SLUG_RESERVED_VALUES:
                raise ValidationError("This value is reserved. Try a different value.")
