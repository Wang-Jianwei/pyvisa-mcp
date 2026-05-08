from __future__ import annotations

from typing import Annotated
from typing import Any

from pydantic import Field

from .config import ServerConfig
from .schemas import AttributeResult, BackendStatus, CloseResourceResult, OpenResourceResult, QueryMessageResult, ReadMessageResult, ResourceInfoResult, VisibleResourcesResult, WriteMessageResult
from .session_registry import SessionRegistry, UnknownSessionError
from .visa_adapter import VisaAdapter, operation_error_from_exception

AttributeValue = str | int | float | bool | None

ResourceQueryArg = Annotated[
    str,
    Field(description="VISA resource query pattern, for example '?*::INSTR' or a more specific interface filter."),
]
ResourceNameArg = Annotated[
    str,
    Field(description="Fully qualified VISA resource name to open or inspect, for example 'TCPIP0::1::INSTR'."),
]
SessionIdArg = Annotated[
    str,
    Field(description="Session identifier returned by open_resource_session and reused by read, write, query, close, and attribute tools."),
]
MessageArg = Annotated[
    str,
    Field(description="Raw instrument command or payload to send through the opened VISA session."),
]
CommandArg = Annotated[
    str,
    Field(description="SCPI or device-specific query command expected to return a response, for example '*IDN?'."),
]
OpenTimeoutArg = Annotated[
    int,
    Field(description="Open timeout in milliseconds used only while establishing the VISA resource handle."),
]
TimeoutArg = Annotated[
    int,
    Field(description="Session I/O timeout in milliseconds applied after the resource opens."),
]
ReadTerminationArg = Annotated[
    str | None,
    Field(description="Optional read termination string such as '\\n'; null leaves the resource default unchanged."),
]
WriteTerminationArg = Annotated[
    str | None,
    Field(description="Optional write termination string such as '\\n'; null leaves the resource default unchanged."),
]
QueryDelayArg = Annotated[
    float | None,
    Field(description="Optional delay in seconds inserted before reading a query response or set as the resource query_delay."),
]
ChunkSizeArg = Annotated[
    int | None,
    Field(description="Optional VISA read chunk size in bytes for the opened resource; null keeps the backend default."),
]
AttributeNameArg = Annotated[
    str,
    Field(description="Python-level or VISA-level attribute name. Common runtime attributes are timeout, read_termination, write_termination, query_delay, and chunk_size."),
]
AttributeValueArg = Annotated[
    AttributeValue,
    Field(description="Attribute value to set. Strings are coerced for common runtime attributes, and 'null'/'none' clear supported termination attributes."),
]

_INTEGER_ATTRIBUTES = {"timeout", "chunk_size"}
_FLOAT_ATTRIBUTES = {"query_delay"}
_STRING_ATTRIBUTES = {"read_termination", "write_termination"}

TOOL_NAMES = [
    "list_visible_resources",
    "get_backend_diagnostics",
    "open_resource_session",
    "close_resource_session",
    "write_message",
    "read_message",
    "query_message",
    "inspect_resource_info",
    "get_resource_attribute",
    "set_resource_attribute",
]


def coerce_attribute_value(attribute: str, value: AttributeValue) -> AttributeValue:
    normalized_attribute = attribute.strip()

    if normalized_attribute in _INTEGER_ATTRIBUTES:
        if value is None:
            if normalized_attribute == "timeout":
                return None
            raise ValueError(f"Attribute '{normalized_attribute}' does not accept null")
        if isinstance(value, bool):
            raise ValueError(f"Attribute '{normalized_attribute}' expects an integer value")
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            raise ValueError(f"Attribute '{normalized_attribute}' expects an integer value")
        return int(value.strip())

    if normalized_attribute in _FLOAT_ATTRIBUTES:
        if value is None:
            raise ValueError(f"Attribute '{normalized_attribute}' does not accept null")
        if isinstance(value, bool):
            raise ValueError(f"Attribute '{normalized_attribute}' expects a numeric value")
        if isinstance(value, (int, float)):
            return float(value)
        return float(value.strip())

    if normalized_attribute in _STRING_ATTRIBUTES:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.lower() in {"none", "null"}:
                return None
            return value
        raise ValueError(f"Attribute '{normalized_attribute}' expects a string or null value")

    return value


def register_tools(
    mcp: Any,
    *,
    adapter: VisaAdapter,
    registry: SessionRegistry,
    config: ServerConfig,
) -> None:
    @mcp.tool(name="list_visible_resources")
    def list_visible_resources(query: ResourceQueryArg = config.default_resource_query) -> VisibleResourcesResult:
        """List VISA resources visible through the configured backend."""
        return adapter.list_visible_resources(query)

    @mcp.tool(name="get_backend_diagnostics")
    def get_backend_diagnostics() -> BackendStatus:
        """Return backend and ResourceManager readiness diagnostics."""
        return adapter.backend_status()

    @mcp.tool(name="open_resource_session")
    def open_resource_session(
        resource_name: ResourceNameArg,
        open_timeout_ms: OpenTimeoutArg = config.default_open_timeout_ms,
        timeout_ms: TimeoutArg = config.default_timeout_ms,
        read_termination: ReadTerminationArg = None,
        write_termination: WriteTerminationArg = None,
        query_delay_s: QueryDelayArg = None,
        chunk_size: ChunkSizeArg = None,
    ) -> OpenResourceResult:
        """Open a VISA resource and register it as an MCP-managed session."""
        try:
            resource = adapter.open_resource(
                resource_name=resource_name,
                open_timeout_ms=open_timeout_ms,
                timeout_ms=timeout_ms,
                read_termination=read_termination,
                write_termination=write_termination,
                query_delay_s=query_delay_s,
                chunk_size=chunk_size,
            )
            session = registry.open(
                resource_name=resource_name,
                resource=resource,
                timeout_ms=timeout_ms,
                read_termination=read_termination,
                write_termination=write_termination,
                query_delay_s=query_delay_s,
                chunk_size=chunk_size,
            )
            return OpenResourceResult(resource_name=resource_name, session=session)
        except Exception as exc:
            return OpenResourceResult(
                resource_name=resource_name,
                error=operation_error_from_exception(exc),
            )

    @mcp.tool(name="close_resource_session")
    def close_resource_session(session_id: SessionIdArg) -> CloseResourceResult:
        """Close a previously opened MCP-managed VISA session."""
        try:
            return registry.close(session_id, close_callback=adapter.close_resource)
        except UnknownSessionError:
            return CloseResourceResult(
                session_id=session_id,
                closed=False,
                error=operation_error_from_exception(
                    UnknownSessionError(session_id),
                    code="unknown_session",
                ),
            )
        except Exception as exc:
            return CloseResourceResult(
                session_id=session_id,
                closed=False,
                error=operation_error_from_exception(exc),
            )

    @mcp.tool(name="write_message")
    def write_message(session_id: SessionIdArg, message: MessageArg) -> WriteMessageResult:
        """Write a message to an opened session."""
        try:
            managed = registry.require(session_id)
            bytes_written = adapter.write_message(managed.resource, message)
            return WriteMessageResult(
                session_id=session_id,
                message=message,
                resource_name=managed.resource_name,
                bytes_written=bytes_written,
            )
        except Exception as exc:
            return WriteMessageResult(
                session_id=session_id,
                message=message,
                error=operation_error_from_exception(exc),
            )

    @mcp.tool(name="read_message")
    def read_message(session_id: SessionIdArg) -> ReadMessageResult:
        """Read a message from an opened session."""
        try:
            managed = registry.require(session_id)
            data = adapter.read_message(managed.resource)
            return ReadMessageResult(
                session_id=session_id,
                resource_name=managed.resource_name,
                data=data,
            )
        except Exception as exc:
            return ReadMessageResult(
                session_id=session_id,
                error=operation_error_from_exception(exc),
            )

    @mcp.tool(name="query_message")
    def query_message(
        session_id: SessionIdArg,
        command: CommandArg,
        delay_s: QueryDelayArg = None,
    ) -> QueryMessageResult:
        """Issue a query command to an opened session and return the response."""
        try:
            managed = registry.require(session_id)
            response = adapter.query_message(managed.resource, command, delay_s=delay_s)
            return QueryMessageResult(
                session_id=session_id,
                command=command,
                resource_name=managed.resource_name,
                delay_s=delay_s,
                response=response,
            )
        except Exception as exc:
            return QueryMessageResult(
                session_id=session_id,
                command=command,
                delay_s=delay_s,
                error=operation_error_from_exception(exc),
            )

    @mcp.tool(name="inspect_resource_info")
    def inspect_resource_info(resource_name: ResourceNameArg) -> ResourceInfoResult:
        """Read extended resource information for a resource name."""
        return adapter.read_resource_info(resource_name)

    @mcp.tool(name="get_resource_attribute")
    def get_resource_attribute(session_id: SessionIdArg, attribute: AttributeNameArg) -> AttributeResult:
        """Read a Python-level or VISA-level attribute from an opened resource."""
        try:
            managed = registry.require(session_id)
            value = adapter.get_attribute(managed.resource, attribute)
            return AttributeResult(
                session_id=session_id,
                attribute=attribute,
                resource_name=managed.resource_name,
                value=value,
            )
        except Exception as exc:
            return AttributeResult(
                session_id=session_id,
                attribute=attribute,
                error=operation_error_from_exception(exc),
            )

    @mcp.tool(name="set_resource_attribute")
    def set_resource_attribute(
        session_id: SessionIdArg,
        attribute: AttributeNameArg,
        value: AttributeValueArg,
    ) -> AttributeResult:
        """Set a Python-level or VISA-level attribute on an opened resource."""
        try:
            managed = registry.require(session_id)
            coerced_value = coerce_attribute_value(attribute, value)
            updated_value = adapter.set_attribute(managed.resource, attribute, coerced_value)
            if attribute == "timeout":
                timeout_ms = None if updated_value is None else int(updated_value)
                registry.update_runtime_settings(session_id, timeout_ms=timeout_ms)
            elif attribute == "read_termination":
                read_termination = None if updated_value is None else str(updated_value)
                registry.update_runtime_settings(session_id, read_termination=read_termination)
            elif attribute == "write_termination":
                write_termination = None if updated_value is None else str(updated_value)
                registry.update_runtime_settings(session_id, write_termination=write_termination)
            elif attribute == "query_delay":
                registry.update_runtime_settings(session_id, query_delay_s=float(updated_value))
            elif attribute == "chunk_size":
                registry.update_runtime_settings(session_id, chunk_size=int(updated_value))
            return AttributeResult(
                session_id=session_id,
                attribute=attribute,
                resource_name=managed.resource_name,
                value=updated_value,
            )
        except Exception as exc:
            return AttributeResult(
                session_id=session_id,
                attribute=attribute,
                error=operation_error_from_exception(exc),
            )
