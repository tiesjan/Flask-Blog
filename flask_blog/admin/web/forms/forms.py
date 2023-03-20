from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app
from flask_wtf import FlaskForm  # type: ignore[import]
from werkzeug.security import check_password_hash
from wtforms import (  # type: ignore[import]
    BooleanField,
    EmailField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import (  # type: ignore[import]
    Email,
    InputRequired,
    Length,
    Optional as InputOptional,
)

from flask_blog.admin.file_uploads import FileCollection
from flask_blog.admin.models import AdminUser
from flask_blog.admin.web.forms.fields import (
    HeaderImageIntegerField,
    MarkdownTextAreaField,
    ProtectedPasswordField,
)
from flask_blog.admin.web.forms.filters import lower, strip_value
from flask_blog.admin.web.forms.validation import SLUG_DESCRIPTION, FileExists, Slug

if TYPE_CHECKING:
    from typing import Any, Optional


class AdminLoginForm(FlaskForm):
    _admin_user = None

    email_address = EmailField(
        "Email address",
        filters=[strip_value, lower],
        validators=[InputRequired(), Email()],
    )
    password = ProtectedPasswordField(
        "Password",
        filters=[],
        validators=[InputRequired()],
    )
    remember = BooleanField(
        "Remember me",
        filters=[],
        validators=[InputOptional()],
    )

    submit_login = SubmitField("Login")

    def validate(self, extra_validators: Optional[Any] = None) -> bool:
        """
        Validates the email address-password combination against entries in the database.

        For validation to succeed, an admin user entry with the email address must be found,
        the password must match and the admin user must be marked as active.

        Once validation succeeds, the `admin_user` property can be accessed to retrieve the data.
        """

        if not super().validate(extra_validators):
            return False

        email_address = self.email_address.data

        admin_user = AdminUser.get_by_email_address(email_address=email_address)
        if (
            admin_user is None
            or not check_password_hash(admin_user.password_hash, self.password.data)
            or not admin_user.is_active
        ):
            self.form_errors.append("Email address or password invalid.")
            current_app.logger.error(f"Invalid login attempt for email address: {email_address}")
            return False

        self._admin_user = admin_user

        return True

    @property
    def admin_user(self) -> AdminUser:
        """
        Returns the AdminUser instance that represents a valid entry in the database.
        """

        if self._admin_user is None:
            raise RuntimeError("Validate form before accessing property `admin_user`.")

        return self._admin_user


class BlogCategoryForm(FlaskForm):
    slug = StringField(
        "URL path for category",
        filters=[strip_value],
        validators=[InputRequired(), Length(max=50), Slug()],
        description=SLUG_DESCRIPTION,
    )
    name = StringField(
        "Name",
        filters=[strip_value],
        validators=[InputRequired(), Length(max=50)],
    )

    save_changes = SubmitField("Save")
    cancel_changes = SubmitField("Go back")


class BlogPostForm(FlaskForm):
    category_id = SelectField(
        "Category",
        coerce=int,
        filters=[strip_value],
        validators=[InputRequired()],
    )
    title = StringField(
        "Title",
        filters=[strip_value],
        validators=[InputRequired(), Length(max=100)],
    )
    slug = StringField(
        "URL path for post",
        filters=[strip_value],
        validators=[InputRequired(), Length(max=100), Slug()],
        description=SLUG_DESCRIPTION,
    )
    content = MarkdownTextAreaField(
        "Content",
        filters=[],
        validators=[InputRequired()],
    )
    tagline = StringField(
        "Tagline",
        filters=[strip_value],
        validators=[InputRequired(), Length(max=100)],
        description="Short description of the post's content.",
    )
    header_image_file_id = HeaderImageIntegerField(
        "Header image",
        filters=[strip_value],
        validators=[InputRequired(), FileExists(file_collection=FileCollection.IMAGES)],
        description="Don't forget to save after changing or clearing the header image.",
    )
    published = BooleanField(
        "Published",
        validators=[InputOptional()],
    )
    featured = BooleanField(
        "Show in featured section",
        validators=[InputOptional()],
    )

    save_changes = SubmitField("Save")
    cancel_changes = SubmitField("Go back")


class ObjectDeleteForm(FlaskForm):
    confirm_delete = SubmitField("Confirm")
    cancel_delete = SubmitField("Go back")
