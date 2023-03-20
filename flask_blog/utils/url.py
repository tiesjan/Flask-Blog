from urllib.parse import urljoin, urlsplit

from flask import request


def is_hosted_url(*, url: str) -> bool:
    """
    Returns whether the given `url` is hosted by this server.

    The given `url` is joined with the host URL to construct an absolute URL. If the given `url`
    contains its own `netloc`, the host's `netloc` will be overwritten by `urljoin`. This allows for
    comparing the `netloc` from both URLs.
    """

    split_url = urlsplit(urljoin(request.host_url, url))
    split_host_url = urlsplit(request.host_url)

    return split_url.netloc == split_host_url.netloc
