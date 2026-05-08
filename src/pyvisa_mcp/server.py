from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from .config import ServerConfig
from .resources import register_resources
from .session_registry import SessionRegistry
from .tools import TOOL_NAMES, register_tools
from .visa_adapter import VisaAdapter


def _preload_pyvisa_import() -> None:
    try:
        import pyvisa  # type: ignore  # noqa: F401
    except Exception:
        return


def create_server(config: ServerConfig | None = None) -> FastMCP:
    config = config or ServerConfig.from_env()
    adapter = VisaAdapter(
        default_backend=config.default_backend,
        preferred_transport=config.preferred_transport,
    )
    registry = SessionRegistry()

    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[None]:
        try:
            yield None
        finally:
            registry.close_all(close_callback=adapter.close_resource)

    mcp = FastMCP(
        config.server_name,
        instructions=config.server_instructions,
        lifespan=lifespan,
        json_response=True,
    )
    register_tools(mcp, adapter=adapter, registry=registry, config=config)
    register_resources(
        mcp,
        adapter=adapter,
        registry=registry,
        config=config,
        tool_names=TOOL_NAMES,
    )
    return mcp


def main() -> None:
    config = ServerConfig.from_env()
    if config.preferred_transport == "stdio":
        _preload_pyvisa_import()
    mcp = create_server(config)
    mcp.run(transport=config.preferred_transport)


if __name__ == "__main__":
    main()
