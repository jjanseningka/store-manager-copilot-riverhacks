"""End-to-end smoke test for the hello-world MCP server.

Spawns the server the same way ``.cursor/mcp.json`` does — via
``uv run --directory mcp-servers/hello-world --frozen python server.py``
— and drives it over stdio using the official MCP Python client. Proves
that:

1. The launch command in `.cursor/mcp.json` actually starts the server.
2. The server registers the expected tools (`hello`, `add`).
3. Each tool returns the expected value for a known input.

Run via ``make smoke-mcp`` or directly with::

    uv run python scripts/smoke-mcp.py

Exits 0 on success, non-zero on any mismatch. Designed for CI as well as
local debugging.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Mirror .cursor/mcp.json exactly so this script breaks the moment that
# config drifts from what actually works. The repo root is the cwd uv
# expects when --directory is relative.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SERVER_PARAMS = StdioServerParameters(
    command="uv",
    args=[
        "--directory",
        "mcp-servers/hello-world",
        "run",
        "--frozen",
        "python",
        "server.py",
    ],
    cwd=str(_REPO_ROOT),
)


def _extract_text(result: object) -> str:
    """Pull the first text payload off an MCP tool-call result.

    MCP tool results wrap their content in a list of typed blocks; we
    only ever expect a single ``TextContent`` here. Fail loudly if the
    shape changes so a real regression cannot hide behind a duck-typed
    ``str(result)``.
    """
    content = getattr(result, "content", None)
    if not content:
        raise AssertionError(f"tool result had no content: {result!r}")
    first = content[0]
    text = getattr(first, "text", None)
    if text is None:
        raise AssertionError(f"tool result first block had no .text: {first!r}")
    return text


async def _drive_server() -> None:
    async with stdio_client(_SERVER_PARAMS) as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        tools = await session.list_tools()
        tool_names = sorted(tool.name for tool in tools.tools)
        expected = ["add", "hello"]
        if tool_names != expected:
            raise AssertionError(f"expected tools {expected}, got {tool_names}")
        print(f"[ok] tools advertised: {tool_names}")

        hello_result = await session.call_tool("hello", {"name": "Cursor"})
        hello_text = _extract_text(hello_result)
        if hello_text != "Hello, Cursor!":
            raise AssertionError(f"hello('Cursor') returned {hello_text!r}")
        print(f"[ok] hello('Cursor') -> {hello_text!r}")

        add_result = await session.call_tool("add", {"a": 17, "b": 25})
        add_text = _extract_text(add_result)
        if add_text != "42":
            raise AssertionError(f"add(17, 25) returned {add_text!r} (expected '42')")
        print(f"[ok] add(17, 25) -> {add_text}")


def main() -> int:
    try:
        asyncio.run(_drive_server())
    except AssertionError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[fail] unexpected error: {exc!r}", file=sys.stderr)
        return 2
    print("hello-world MCP smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
