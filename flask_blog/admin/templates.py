from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Markup, render_template

if TYPE_CHECKING:
    from typing import Any, Sequence

    from wtforms import FormField, ValidationError  # type: ignore[import]


def render_admin_form_errors(errors: Sequence[ValidationError]) -> Markup:
    """
    Template global that renders the given admin form errors using a partial template.
    """

    template_name = "admin/partials/form_errors.html"
    template_context = {"errors": errors}

    return Markup(render_template(template_name, **template_context))


def render_admin_form_field(form_field: FormField, **kwargs: Any) -> Markup:
    """
    Template global that renders the given admin form field using a partial template.

    Any given kwargs are forwarded when rendering the field instance.
    """

    if len(form_field.errors) > 0:
        kwargs["aria_invalid"] = "true"

    template_name = "admin/partials/form_field.html"
    template_context = {"form_field": form_field, "kwargs": kwargs}

    return Markup(render_template(template_name, **template_context))


def render_admin_truthy_icon(value: bool) -> Markup:
    """
    Template global that renders an icon based on the value's truthiness.
    """

    if value is True:
        classes = "bi bi-check-circle-fill text-success"
    else:
        classes = "bi bi-circle text-secondary"

    return Markup(f'<i class="{classes}"></i>')
