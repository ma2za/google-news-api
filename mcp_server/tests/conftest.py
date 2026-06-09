"""Test setup for the MCP server.

``mcp_server`` is a plain script directory (no package), and importing
``googlenews`` pulls in heavy, network-oriented dependencies (aiohttp,
trafilatura, mcp) that the pure helpers under test do not use. Make the module
importable and stub those optional dependencies so the tests run anywhere
without installing them.
"""

import sys
import types
from pathlib import Path

# Make googlenews.py importable as a top-level module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Stub heavy optional dependencies that are only used by network code paths.
for _name in ("aiohttp", "trafilatura"):
    sys.modules.setdefault(_name, types.ModuleType(_name))

# ``aiohttp.ClientSession`` is referenced in a function annotation evaluated at
# import time, so the stub needs the attribute to exist.
if not hasattr(sys.modules["aiohttp"], "ClientSession"):
    sys.modules["aiohttp"].ClientSession = object

if "mcp.server.fastmcp" not in sys.modules:
    _mcp = types.ModuleType("mcp")
    _server = types.ModuleType("mcp.server")
    _fastmcp = types.ModuleType("mcp.server.fastmcp")

    class _FakeFastMCP:
        def __init__(self, *args, **kwargs):
            pass

        def tool(self, *args, **kwargs):
            def _decorator(fn):
                return fn

            return _decorator

        def run(self, *args, **kwargs):
            pass

    _fastmcp.FastMCP = _FakeFastMCP
    _server.fastmcp = _fastmcp
    _mcp.server = _server
    sys.modules["mcp"] = _mcp
    sys.modules["mcp.server"] = _server
    sys.modules["mcp.server.fastmcp"] = _fastmcp
