from enum import Enum, auto
from typing import Optional, Union
from urllib.parse import urlparse

import bleach  # type: ignore[import]
import markdown  # type: ignore[import]
from bleach.callbacks import target_blank  # type: ignore[import]

LinkifyAttributes = dict[Union[tuple[Optional[str], str], str], str]

ALLOWED_HTML_TAGS = {
    "p",
    "div",
    "span",
    "br",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "code",
    "pre",
    "strong",
    "em",
    "sub",
    "sup",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "ul",
    "ol",
    "li",
    "a",
    "img",
    "hr",
}

ALLOWED_HTML_ATTRS = {
    "*": {"id"},
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "title"},
}

ALLOWED_PROTOCOLS = {
    "http",
    "https",
    "mailto",
}

LINKIFY_SKIP_TAGS = {
    "code",
    "pre",
}


class LinkTarget(Enum):
    BLANK = auto()


def allowed_protocols(  # pylint: disable=unused-argument
    attrs: LinkifyAttributes,
    new: bool = False,
) -> Optional[LinkifyAttributes]:
    """
    Callback for Bleach linkify that determines whether the link protocol is allowed.
    """

    href_key = (None, "href")
    href = attrs.get(href_key, "")

    try:
        parsed_url = urlparse(href)
    except ValueError:
        pass
    else:
        if parsed_url.scheme in ALLOWED_PROTOCOLS:
            return attrs

    return None


def markdown_to_html(*, markdown_text: str, link_target: Optional[LinkTarget] = None) -> str:
    """
    Renders given Markdown text to sanitized HTML text.

    Automatically linkifies bare URLs found given text. If `link_target` is given, updates link
    targets accordingly.
    """

    rendered_html_text: str = markdown.markdown(text=markdown_text, output_format="html")

    if link_target is LinkTarget.BLANK:
        linkify_callbacks = [target_blank, allowed_protocols]
    else:
        linkify_callbacks = [allowed_protocols]

    linkified_html_text: str = bleach.linkify(
        text=rendered_html_text,
        callbacks=linkify_callbacks,
        skip_tags=LINKIFY_SKIP_TAGS,
        parse_email=True,
    )

    sanitized_html_text: str = bleach.clean(
        text=linkified_html_text,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )

    return sanitized_html_text
