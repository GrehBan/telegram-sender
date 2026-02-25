from pyrogram.errors import RPCError


def resolve_timeout(error: Exception | None, default: float = 0.0) -> float:
    """Safely extract a timeout value from an error.

    If the error is an ``RPCError`` with a numeric ``value``
    attribute (e.g., flood-wait), that value is returned.
    Otherwise, the default is returned.

    Args:
        error: The exception to inspect.
        default: The fallback value if no timeout is found.

    Returns:
        The extracted timeout or the default.
    """
    if isinstance(error, RPCError) and isinstance(error.value, (int, float)):
        return max(float(error.value), default)
    return default
