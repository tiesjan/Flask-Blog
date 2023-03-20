from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from flask import Markup, render_template, url_for
from wtforms import IntegerField, PasswordField, TextAreaField  # type: ignore[import]
from wtforms.validators import Length, StopValidation, ValidationError  # type: ignore[import]
from wtforms.widgets import HiddenInput  # type: ignore[import]

from flask_blog.blog.models import File
from flask_blog.database.core import db

if TYPE_CHECKING:
    from typing import Any, Iterable

    from flask_wtf import FlaskForm  # type: ignore[import]


EMPTY_IMAGE_DATA_URL = (
    "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


class HeaderImageIntegerField(IntegerField):
    """
    Hidden input field for selecting the File primary key of a header image, with a small image
    preview box.

    If no image is selected, this is indicated using a transparent pixel in the preview.
    """

    widget = HiddenInput()

    def __call__(self, **kwargs: Any) -> str:
        """
        Renders the HeaderImageIntegerField for use in HTML templates.
        """

        integer_field = self
        rendered_integer_field = super().__call__(**kwargs)

        image_url = EMPTY_IMAGE_DATA_URL
        if self.data is not None:
            file = (
                db.session.query(File.collection, File.filename)
                .filter(File.id == self.data)
                .first()
            )
            if file is not None:
                image_url = url_for(
                    "serve_media_file", collection=file.collection, filename=file.filename
                )

        template_name = "admin/partials/header_image_integer_field.html"
        template_context = {
            "empty_image_data_url": Markup(EMPTY_IMAGE_DATA_URL),
            "image_url": Markup(image_url),
            "integer_field": integer_field,
            "rendered_integer_field": rendered_integer_field,
        }

        return Markup(render_template(template_name, **template_context))


class MarkdownTextAreaField(TextAreaField):
    """
    TextArea field for Markdown content, with a preview that can be toggled.

    Requires the static files `markdown-editor.css` and `markdown-editor.js` to be included in HTML
    templates that render this field.
    """

    def __call__(self, **kwargs: Any) -> str:
        """
        Renders the MarkdownTextAreaField for use in HTML templates.
        """

        textarea_field = self
        rendered_textarea_field = super().__call__(**kwargs)

        template_name = "admin/partials/markdown_textarea_field.html"
        template_context = {
            "textarea_field": textarea_field,
            "rendered_textarea_field": rendered_textarea_field,
        }

        return Markup(render_template(template_name, **template_context))


class ProtectedPasswordField(PasswordField):
    """
    Password field with extra field data processing and security measures.
    """

    maximum_password_length = 1024

    def pre_validate(self, form: FlaskForm) -> None:
        """
        Limit passwords to a reasonable length to prevent DDOS attacks. These can occur when key
        derivation functions re-hash the password several times and the data to hash is large.
        """

        if self.data is not None:
            validate_length = Length(max=self.maximum_password_length)
            try:
                validate_length(form, self)
            except ValidationError as exception:
                raise StopValidation(str(exception)) from exception

        super().pre_validate(form)

    def process_formdata(self, valuelist: Iterable[str]) -> None:
        """
        Normalize the submitted form data to ensure passwords are hashed using the same unicode data
        form.
        """

        valuelist = [unicodedata.normalize("NFKD", value) for value in valuelist]

        super().process_formdata(valuelist)
