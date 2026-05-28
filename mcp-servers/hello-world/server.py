"""Hello-world MCP server.

Smallest useful MCP server: one greeting tool, one add tool. Demonstrates
the request/response loop end-to-end with no credentials and no network.

Dependencies and tool metadata live in `pyproject.toml`. Run via:

    uv run --directory mcp-servers/hello-world python server.py

The default launcher in `.cursor/mcp.json` does this for you on Cursor
startup. See `README.md` for how to add your own tool.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello-world")


@mcp.tool()
def hello(name: str = "world") -> str:
    """Return a friendly greeting.

    Args:
        name: Who to greet. Defaults to ``"world"``.
    """
    return f"Hello, {name}!"


@mcp.tool()
def add(a: int, b: int) -> int:
    """Return the sum of two integers.

    The smallest possible "the agent called my tool with arguments and
    got a structured answer back" demo.
    """
    return a + b


def main() -> None:
    """Entry point for the ``hello-world-mcp`` console script."""
    mcp.run()


if __name__ == "__main__":
    main()
