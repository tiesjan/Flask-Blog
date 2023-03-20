from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.types import DateTime, TypeDecorator

if TYPE_CHECKING:
    from typing import Any, Optional

    from sqlalchemy.engine import Dialect


class TZDateTime(TypeDecorator[datetime]):
    """
    DateTime data type for transparently handling timezones.

    Values are stored as naive UTC timestamps and returned as aware local timestamps.

    Requires timezone aware `datetime` objects to be used in queries.
    """

    impl = DateTime(timezone=False)
    cache_ok = True

    def process_bind_param(self, value: Optional[datetime], dialect: Dialect) -> Optional[datetime]:
        """
        Processes timezone aware `datetime` objects for use in queries.

        The given `value` is converted to a naive `datetime` object in the UTC timezone.
        """

        if value is not None:
            if value.tzinfo is None:
                raise ValueError("Timezone aware `datetime` object is required.")

            value = value.astimezone(timezone.utc).replace(tzinfo=None)

        return value

    def process_literal_param(self, value: Optional[Any], dialect: Dialect) -> str:
        """
        Renders the given Python `value` into a literal string, for use in SQL query previews.

        Processes the value as for bound parameters and returns it in ISO-8601 string format.
        """

        bound_value = self.process_bind_param(value=value, dialect=dialect)

        if bound_value is not None:
            return bound_value.isoformat(sep="T")

        return str(bound_value)

    def process_result_value(
        self, value: Optional[datetime], dialect: Dialect
    ) -> Optional[datetime]:
        """
        Processes naive `datetime` objects returned in query results.

        The given `value` is converted to an aware `datetime` object in the local timezone.
        """

        if value is not None:
            if value.tzinfo is not None:
                raise ValueError("Naive `datetime` object is required.")

            value = value.replace(tzinfo=timezone.utc).astimezone()

        return value

    @property
    def python_type(self) -> type:
        """
        Returns the Python type used for parameter and result values.
        """

        return type(self.impl.python_type)
