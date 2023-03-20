from __future__ import annotations

import hashlib
import itertools
import os
import re
import shutil
import tempfile
import uuid
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import magic
from flask import current_app
from sqlalchemy import or_, select
from sqlalchemy.exc import DBAPIError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from flask_blog.blog.models import File
from flask_blog.database.core import db
from flask_blog.database.functions import escape_value
from flask_blog.utils.url import is_hosted_url

if TYPE_CHECKING:
    from typing import Sequence


class FileCollection(Enum):
    IMAGES = "images"


FILE_COLLECTION_REGEX = f"{'|'.join(re.escape(collection.value) for collection in FileCollection)}"

IMAGE_URL_REGEXES = (
    # ![ALT_TEXT](https://www.example.com/image.jpg)
    re.compile(r"!\[[^]]*]\(\s*([^\s)]+)\s*\)"),
    # ![ALT_TEXT](<https://www.example.com/image.jpg>)
    re.compile(r"!\[[^]]*]\(\s*<\s*([^\s>)]+)\s*>\s*\)"),
    # [LINK_REF]: https://www.example.com/image.jpg
    re.compile(r"^\[[^]]+]:\s+((?!<)\S+(?<!>))\s*$", re.MULTILINE),
    # [LINK_REF]: <https://www.example.com/image.jpg>
    re.compile(r"^\[[^]]+]:\s+<([^>\s]+)>\s*$", re.MULTILINE),
)


def detect_file_references(*, markdown_text: str) -> Sequence[File]:
    """
    Returns a sequence of File instances that the given `markdown_text` refers to.

    First retrieves all Markdown URLs, then retrieves all File instances from the database matching
    the collection and filenames encoded in those URLs.
    """

    all_image_urls = itertools.chain.from_iterable(
        re.findall(regex, markdown_text) for regex in IMAGE_URL_REGEXES
    )

    media_url_prefix = re.escape(current_app.config["MEDIA_URL_PREFIX"].strip("/"))
    hosted_file_path_regex = re.compile(
        # /<media_url_prefix>/<collection>/<filename>
        rf"^/+{media_url_prefix}/+({FILE_COLLECTION_REGEX})/+([^/]+)$"
    )

    filter_clauses = []

    for image_url in all_image_urls:
        if is_hosted_url(url=image_url):
            split_image_url = urlsplit(image_url)
            match = re.search(hosted_file_path_regex, split_image_url.path)
            if match is not None:
                collection, filename = match.groups()
                filter_clauses.append((File.collection == collection) & (File.filename == filename))

    if len(filter_clauses) == 0:
        return []

    return db.session.query(File).filter(or_(*filter_clauses)).all()


def file_exists(*, filename: str, file_collection: FileCollection) -> bool:
    """
    Returns whether a file with the given filename exists in the database.
    """

    escape_char = "\\"

    escaped_filename = escape_value(value=filename, chars=("%", "_"), escape_char=escape_char)

    file_exists_query = (
        select(File.id)
        .filter(
            (File.filename.ilike(escaped_filename, escape=escape_char)),
            (File.collection == file_collection.value),
        )
        .exists()
    )

    result: bool = db.session.query(file_exists_query).scalar()

    return result


def normalize_filename(*, filename: str, file_collection: FileCollection) -> str:
    """
    Normalizes the given filename securely.

    The given filename is expected to have the format `<name>.<ext>`. The name and the extension are
    securely normalized separately. Characters that cannot be normalized (e.g. CJK characters) are
    simply removed. This may lead to an empty name or an empty extension. Empty names are replaced
    with a UUID4 string, empty extensions fall back to `txt` for serving them as plain text files.

    In case a normalized filename already exists in the database, the suffix `-<n>`, where <n> is an
    integer, is added to the name part.
    """

    name, extension = os.path.splitext(filename)

    if extension == "":
        raise ValueError(f"Expected filename format: <name>{os.path.extsep}<ext>, got: {filename}")

    name = secure_filename(name) or uuid.uuid4().hex
    extension = secure_filename(extension) or "txt"

    # Enforce maximum filename length
    max_name_length = File.MAX_FILENAME_LENGTH - (len(os.path.extsep) + len(extension))
    if len(name) > max_name_length:
        name = name[:max_name_length]

    filename = os.path.extsep.join([name, extension])

    suffix = 0
    while file_exists(filename=filename, file_collection=file_collection):
        suffix += 1

        if suffix == 1:
            # Once the first suffix is to be appended, enforce a reduced maximum name length to
            # accommodate for suffices "-1" through "-99".
            max_name_length -= 3
            if len(name) > max_name_length:
                name = name[:max_name_length]

        elif suffix > 99:
            raise RuntimeError("Attempted 99 suffices. Stopping to prevent resource exhaustion.")

        filename = os.path.extsep.join([f"{name[:max_name_length]}-{suffix}", extension])

    return filename


def store_file(*, file: FileStorage, file_collection: FileCollection) -> tuple[File, bool]:
    """
    Takes the given file storage, stores its data on disk and registers the file in the database.

    Returns a tuple of:
      - the File entry registered in the database
      - a boolean indicating whether the file is new (True) or already existed (False)

    The data is read in chunks and stored in a temporary file. While going over those chunks, the
    mimetype, the size and the content hash of the data is determined. If an existing file with an
    identical content hash is found in the database, that entry is returned without further
    processing. Otherwise, the temporary file is copied over to the destination file and the new
    database entry is returned.

    Note: the given file storage is expected to have a filename set, or else this function cannot
    determine how to store the data to disk.
    """

    if file.filename is None:
        raise ValueError("Given FileStorage does not have a filename set.")

    mimetype = ""
    content_size = 0
    content_hasher = hashlib.sha256()

    with tempfile.NamedTemporaryFile() as temporary_file:
        num_chunks_read = 0
        while chunk := file.stream.read(8192):
            num_chunks_read += 1

            if num_chunks_read == 0:
                # Recommended to read at least the first 2048 bytes for reliable detection
                mimetype = magic.from_buffer(chunk, mime=True)

            content_size += len(chunk)
            content_hasher.update(chunk)
            temporary_file.write(chunk)

        content_hash = content_hasher.hexdigest()

        # If an existing file with an identical content has exists, return that instead
        stored_file = db.session.query(File).filter(File.content_hash == content_hash).scalar()
        if stored_file is not None:
            return stored_file, False

        media_dir = Path(current_app.config["MEDIA_DIR"])
        collection_path = media_dir / file_collection.value
        if not collection_path.exists():
            collection_path.mkdir()

        filename = normalize_filename(filename=file.filename, file_collection=file_collection)
        file_path = collection_path / filename

        temporary_file.seek(0)
        with open(file_path, "wb") as destination_file:
            shutil.copyfileobj(temporary_file, destination_file)

        stored_file = File(
            filename=filename,
            collection=file_collection.value,
            mimetype=mimetype,
            content_size=content_size,
            content_hash=content_hash,
        )

        try:
            db.session.add(stored_file)
            db.session.commit()
        except DBAPIError:
            # Delete destination file on failure
            file_path.unlink(missing_ok=True)
            raise

        return stored_file, True
