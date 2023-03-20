from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Sequence

    from sqlalchemy.engine.default import DefaultExecutionContext
    from sqlalchemy.sql.schema import Column


def escape_value(*, value: str, chars: Sequence[str], escape_char: str) -> str:
    """
    Returns an escaped `value` by prepending each of the given `chars` with the given `escape_char`.

    This allows for escaping a value when using operators such as (I)LIKE.
    """

    for char in chars:
        value = value.replace(char, f"{escape_char}{char}")

    return value


def from_column(column: Column[Any]) -> Callable[[DefaultExecutionContext], Any]:
    """
    Returns a context-sensitive function that returns the Pythonic value from another column.

    This allows for setting a (default) value in one column that is automatically copied over to
    another column.
    """

    def context_sensitive_default(context: DefaultExecutionContext) -> Any:
        return context.get_current_parameters().get(column.name)

    return context_sensitive_default
