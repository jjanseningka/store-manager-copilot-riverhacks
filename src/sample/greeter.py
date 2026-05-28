"""Minimal sample module so the test suite has something to verify.

Replace this with real code when you adapt the starter to your project.
"""


def greet(name: str) -> str:
    """Return a friendly greeting for ``name``.

    Raises:
        ValueError: If ``name`` is empty or whitespace-only. Fail fast at the
            boundary rather than producing a nonsensical "Hello, !".
    """
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("name must not be empty or whitespace")
    return f"Hello, {cleaned}!"
