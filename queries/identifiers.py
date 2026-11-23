"""Quote SQL identifiers separately from bound values; reject SQL fragments."""

import re

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def identifier(engine, name: str, *, qualified: bool = False) -> str:
    parts = name.split(".") if isinstance(name, str) else []
    if (
        not parts
        or len(parts) > (2 if qualified else 1)
        or any(not _IDENTIFIER.fullmatch(part) for part in parts)
    ):
        raise ValueError("Expected a simple SQL identifier, not a SQL expression")
    return ".".join(engine.dialect.identifier_preparer.quote(part) for part in parts)


def pagination(page: int, page_size: int) -> int:
    if type(page) is not int or page < 1:
        raise ValueError("page must be a positive integer")
    if type(page_size) is not int or not 1 <= page_size <= 1000:
        raise ValueError("page_size must be between 1 and 1000")
    return (page - 1) * page_size


def simple_identifier(name: str) -> str:
    """Validate a single identifier for APIs that perform their own quoting."""
    if not isinstance(name, str) or not _IDENTIFIER.fullmatch(name):
        raise ValueError("Expected a simple identifier, not an expression")
    return name
