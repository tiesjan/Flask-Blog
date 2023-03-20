from __future__ import annotations

from flask_wtf import FlaskForm  # type: ignore[import]
from flask_wtf.file import FileAllowed, FileField, FileRequired  # type: ignore[import]
from wtforms import SubmitField  # type: ignore[import]

from flask_blog.admin.api.forms.validation import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_IMAGE_MIMETYPES,
    ALLOWED_IMAGE_MIMETYPES_DESCRIPTION,
    MIMETypeAllowed,
)


class ImageUploadForm(FlaskForm):
    image_file = FileField(
        "Image file",
        validators=[
            FileRequired(),
            FileAllowed(upload_set=ALLOWED_IMAGE_EXTENSIONS),
            MIMETypeAllowed(allowed_mimetypes=ALLOWED_IMAGE_MIMETYPES),
        ],
        description=ALLOWED_IMAGE_MIMETYPES_DESCRIPTION,
        render_kw={"accept": ",".join(ALLOWED_IMAGE_MIMETYPES)},
    )

    submit_upload = SubmitField("Start upload")
