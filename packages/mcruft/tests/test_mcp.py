# this_file: packages/mcruft/tests/test_mcp.py
import asyncio
import builtins
import sys
from contextlib import asynccontextmanager
from types import ModuleType

import pytest
from mcruft import EngineUnavailable
from mcruft.mcp import McpSession


def test_open_when_extra_missing_then_explains_install(monkeypatch, tmp_path):
    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == "mcp":
            raise ImportError("not installed")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    with pytest.raises(EngineUnavailable, match=r"mcruft\[mcp\]"):
        asyncio.run(McpSession().open(tmp_path / "fake", tmp_path, tmp_path))


def test_session_when_stdio_mock_then_opens_calls_and_closes(monkeypatch, tmp_path):
    events = []

    class Parameters:
        def __init__(self, **kwargs):
            events.append(kwargs)

    @asynccontextmanager
    async def transport(params):
        yield "read", "write"
        events.append("transport closed")

    class Session:
        def __init__(self, read, write):
            assert (read, write) == ("read", "write")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            events.append("session closed")

        async def initialize(self):
            events.append("initialized")

        async def call_tool(self, tool, args):
            return {"tool": tool, "args": args}

    sdk, client, stdio = ModuleType("mcp"), ModuleType("mcp.client"), ModuleType("mcp.client.stdio")
    sdk.ClientSession, sdk.StdioServerParameters = Session, Parameters
    stdio.stdio_client = transport
    for name, module in [("mcp", sdk), ("mcp.client", client), ("mcp.client.stdio", stdio)]:
        monkeypatch.setitem(sys.modules, name, module)

    async def check():
        session = await McpSession().open(tmp_path / "vectorcraft-cli", tmp_path, tmp_path)
        async with session:
            assert await session.call("info", {}) == {"tool": "info", "args": {}}

    asyncio.run(check())
    assert "--headless" in events[0]["args"]
    assert events[-2:] == ["session closed", "transport closed"]


def test_session_when_local_stdio_server_then_official_sdk_round_trip(tmp_path):
    pytest.importorskip("mcp")
    binary = tmp_path / "vectorcraft-cli"
    binary.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        "for line in sys.stdin:\n"
        "    request = json.loads(line)\n"
        "    if 'id' not in request: continue\n"
        "    method = request['method']\n"
        "    if method == 'initialize':\n"
        "        result = {'protocolVersion': request['params']['protocolVersion'],\n"
        "                  'capabilities': {'tools': {}},\n"
        "                  'serverInfo': {'name': 'fixture', 'version': '1.0.0'}}\n"
        "    elif method == 'tools/list':\n"
        "        result = {'tools': [{'name': 'echo', 'description': 'echo',\n"
        "                  'inputSchema': {'type': 'object', 'properties': {}}}]}\n"
        "    else:\n"
        "        result = {'content': [{'type': 'text', 'text': 'hello'}]}\n"
        "    print(json.dumps({'jsonrpc': '2.0', 'id': request['id'],\n"
        "                      'result': result}), flush=True)\n"
    )
    binary.chmod(0o755)

    async def check():
        async with asyncio.timeout(15):
            async with await McpSession().open(binary, tmp_path, tmp_path) as session:
                result = await session.call("echo", {})
                assert result.content[0].text == "hello"

    asyncio.run(check())
