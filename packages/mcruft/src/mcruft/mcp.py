# this_file: packages/mcruft/src/mcruft/mcp.py
from __future__ import annotations

from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Self

from .report import EngineUnavailable


class McpSession:
    """An async stdio session; open, call and close in the same asyncio task."""

    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._session: Any = None

    async def open(
        self,
        product_cli_path: Path,
        read_root: Path,
        write_root: Path,
        extra_args: list[str] | None = None,
    ) -> McpSession:
        if self._session is not None:
            raise RuntimeError("MCP session is already open")
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise EngineUnavailable("Install mcruft[mcp] to use MCP sessions") from exc
        binary = Path(product_cli_path).absolute()
        args = [
            "mcp",
            "--automation-read-root",
            str(Path(read_root).absolute()),
            "--automation-write-root",
            str(Path(write_root).absolute()),
        ]
        if binary.name == "vectorcraft-cli":
            args.append("--headless")
        args.extend(extra_args or [])
        try:
            read, write = await self._stack.enter_async_context(
                stdio_client(StdioServerParameters(command=str(binary), args=args))
            )
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self._session = session
        except BaseException:
            await self.close()
            raise
        return self

    async def call(self, tool: str, args: dict[str, Any]) -> Any:
        if self._session is None:
            raise EngineUnavailable("MCP session is not open")
        return await self._session.call_tool(tool, args)

    async def close(self) -> None:
        try:
            await self._stack.aclose()
        finally:
            self._session = None

    async def __aenter__(self) -> Self:
        if self._session is None:
            raise EngineUnavailable("Open the MCP session before entering its context")
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()
