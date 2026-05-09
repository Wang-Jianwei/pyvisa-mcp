from __future__ import annotations

import base64
from pathlib import Path
import tempfile
from typing import Annotated
from typing import Any
from typing import Literal

from pydantic import Field

from .config import ServerConfig
from .schemas import AttributeResult, BackendStatus, BinaryPayloadReference, CloseResourceResult, OpenResourceResult, QueryBinaryMessageResult, QueryMessageResult, ReadBinaryMessageResult, ReadMessageResult, ResourceInfoResult, VisibleResourcesResult, WriteBinaryMessageResult, WriteMessageResult
from .session_registry import SessionRegistry, UnknownSessionError
from .visa_adapter import VisaAdapter, operation_error_from_exception

AttributeValue = str | int | float | bool | None

ResourceQueryArg = Annotated[
    str,
    Field(
        description="VISA resource query pattern, for example '?*::INSTR' or a more specific interface filter.",
        examples=["?*::INSTR", "TCPIP?*::INSTR"],
    ),
]
ResourceNameArg = Annotated[
    str,
    Field(
        description="Fully qualified VISA resource name to open or inspect, for example 'TCPIP0::1::INSTR'.",
        examples=["TCPIP0::1::INSTR", "ASRL2::INSTR"],
    ),
]
SessionIdArg = Annotated[
    str,
    Field(
        description="Session identifier returned by open_resource_session and reused by read, write, query, close, and attribute tools.",
        examples=["12345678-1234-4123-8123-123456789abc"],
    ),
]
MessageArg = Annotated[
    str,
    Field(
        description="Raw instrument command or payload to send through the opened VISA session.",
        examples=["*RST", "SYST:ERR?"],
    ),
]
CommandArg = Annotated[
    str,
    Field(
        description="SCPI or device-specific query command expected to return a response, for example '*IDN?'.",
        examples=["*IDN?", "MEAS:VOLT?"],
    ),
]
OpenTimeoutArg = Annotated[
    int,
    Field(
        description="Open timeout in milliseconds used only while establishing the VISA resource handle.",
        examples=[0, 5000],
    ),
]
TimeoutArg = Annotated[
    int,
    Field(
        description="Session I/O timeout in milliseconds applied after the resource opens.",
        examples=[2000, 10000],
    ),
]
ReadTerminationArg = Annotated[
    str | None,
    Field(
        description="Optional read termination string such as '\\n'; null leaves the resource default unchanged.",
        examples=["\n", None],
    ),
]
WriteTerminationArg = Annotated[
    str | None,
    Field(
        description="Optional write termination string such as '\\n'; null leaves the resource default unchanged.",
        examples=["\n", None],
    ),
]
QueryDelayArg = Annotated[
    float | None,
    Field(
        description="Optional delay in seconds inserted before reading a query response or set as the resource query_delay.",
        examples=[0.1, 0.5],
    ),
]
ChunkSizeArg = Annotated[
    int | None,
    Field(
        description="Optional VISA read chunk size in bytes for the opened resource; null keeps the backend default.",
        examples=[20480, 4096],
    ),
]
AttributeNameArg = Annotated[
    str,
    Field(
        description="Python-level or VISA-level attribute name. Common runtime attributes are timeout, read_termination, write_termination, query_delay, and chunk_size.",
        examples=["timeout", "read_termination", "chunk_size"],
    ),
]
AttributeValueArg = Annotated[
    AttributeValue,
    Field(
        description="Attribute value to set. Strings are coerced for common runtime attributes, and 'null'/'none' clear supported termination attributes.",
        examples=["3000", "\n", "null"],
    ),
]
BinaryPayloadModeArg = Annotated[
    Literal["base64", "temp_file"],
    Field(
        description="Binary payload transport mode. Use 'base64' for inline JSON-safe transport or 'temp_file' to read from or return a server-local file path.",
        examples=["base64", "temp_file"],
    ),
]
BinaryDataBase64Arg = Annotated[
    str | None,
    Field(
        description="Base64-encoded binary payload used when payload_mode is 'base64'.",
        examples=["AQID", "AAECaGVsbG8="],
    ),
]
BinaryFilePathArg = Annotated[
    str | None,
    Field(
        description="Local file path used when payload_mode is 'temp_file'. For reads and binary queries this is populated in the result, not the request.",
        examples=["C:/Temp/instrument.bin"],
    ),
]
BinaryOutputFilePathArg = Annotated[
    str | None,
    Field(
        description="Optional caller-managed file path for binary read or query output when payload_mode is 'temp_file'. When omitted, the server creates and later cleans up a temporary file.",
        examples=["D:/captures/waveform.bin", None],
    ),
]
BinaryOutputConflictArg = Annotated[
    Literal["error", "overwrite"],
    Field(
        description="Conflict policy for output_file_path. Use 'error' to refuse overwriting an existing file or 'overwrite' to replace it.",
        examples=["error", "overwrite"],
    ),
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
    "write_binary_message",
    "read_binary_message",
    "query_binary_message",
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


def _decode_binary_input(
    *,
    payload_mode: Literal["base64", "temp_file"],
    data_base64: str | None,
    file_path: str | None,
) -> bytes:
    if payload_mode == "base64":
        if data_base64 is None:
            raise ValueError("base64 payload_mode requires data_base64")
        try:
            return base64.b64decode(data_base64, validate=True)
        except Exception as exc:
            raise ValueError("Invalid base64 payload") from exc

    if not file_path:
        raise ValueError("temp_file payload_mode requires file_path")
    return Path(file_path).read_bytes()


def _encode_binary_output(
    *,
    session_id: str,
    payload_mode: Literal["base64", "temp_file"],
    payload: bytes,
    registry: SessionRegistry,
    output_file_path: str | None = None,
    output_file_conflict: Literal["error", "overwrite"] = "error",
) -> BinaryPayloadReference:
    if payload_mode == "base64":
        if output_file_path is not None:
            if output_file_conflict != "error":
                raise ValueError("output_file_path and output_file_conflict require payload_mode temp_file")
            raise ValueError("output_file_path requires payload_mode temp_file")
        if output_file_conflict != "error":
            raise ValueError("output_file_path and output_file_conflict require payload_mode temp_file")
        return BinaryPayloadReference(
            payload_mode=payload_mode,
            byte_count=len(payload),
            data_base64=base64.b64encode(payload).decode("ascii"),
            cleanup_on_close=None,
        )

    if output_file_path is not None:
        target_path = Path(output_file_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists() and output_file_conflict != "overwrite":
            raise FileExistsError(f"Output file already exists: {target_path}")
        target_path.write_bytes(payload)
        return BinaryPayloadReference(
            payload_mode=payload_mode,
            byte_count=len(payload),
            file_path=str(target_path),
            cleanup_on_close=False,
        )

    temp_dir = Path(tempfile.gettempdir()) / "pyvisa-mcp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        delete=False,
        dir=temp_dir,
        prefix=f"{session_id}-",
        suffix=".bin",
    ) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    registry.register_temp_file(session_id, temp_path)
    return BinaryPayloadReference(
        payload_mode=payload_mode,
        byte_count=len(payload),
        file_path=str(temp_path),
        cleanup_on_close=True,
    )


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

    @mcp.tool(name="write_binary_message")
    def write_binary_message(
        session_id: SessionIdArg,
        payload_mode: BinaryPayloadModeArg = "base64",
        data_base64: BinaryDataBase64Arg = None,
        file_path: BinaryFilePathArg = None,
    ) -> WriteBinaryMessageResult:
        """Write binary bytes to an opened session from base64 data or a local file."""
        try:
            managed = registry.require(session_id)
            payload = _decode_binary_input(
                payload_mode=payload_mode,
                data_base64=data_base64,
                file_path=file_path,
            )
            bytes_written = adapter.write_binary_message(managed.resource, payload)
            return WriteBinaryMessageResult(
                session_id=session_id,
                payload_mode=payload_mode,
                resource_name=managed.resource_name,
                bytes_written=bytes_written,
            )
        except Exception as exc:
            return WriteBinaryMessageResult(
                session_id=session_id,
                payload_mode=payload_mode,
                error=operation_error_from_exception(exc),
            )

    @mcp.tool(name="read_binary_message")
    def read_binary_message(
        session_id: SessionIdArg,
        payload_mode: BinaryPayloadModeArg = "base64",
        output_file_path: BinaryOutputFilePathArg = None,
        output_file_conflict: BinaryOutputConflictArg = "error",
    ) -> ReadBinaryMessageResult:
        """Read binary bytes from an opened session as base64 or a temporary file reference."""
        try:
            managed = registry.require(session_id)
            payload = adapter.read_binary_message(managed.resource)
            return ReadBinaryMessageResult(
                session_id=session_id,
                resource_name=managed.resource_name,
                payload=_encode_binary_output(
                    session_id=session_id,
                    payload_mode=payload_mode,
                    payload=payload,
                    registry=registry,
                    output_file_path=output_file_path,
                    output_file_conflict=output_file_conflict,
                ),
            )
        except Exception as exc:
            return ReadBinaryMessageResult(
                session_id=session_id,
                error=operation_error_from_exception(exc),
            )

    @mcp.tool(name="query_binary_message")
    def query_binary_message(
        session_id: SessionIdArg,
        command: CommandArg,
        payload_mode: BinaryPayloadModeArg = "base64",
        delay_s: QueryDelayArg = None,
        output_file_path: BinaryOutputFilePathArg = None,
        output_file_conflict: BinaryOutputConflictArg = "error",
    ) -> QueryBinaryMessageResult:
        """Issue a text query command and return a binary response as base64 or a temporary file reference."""
        try:
            managed = registry.require(session_id)
            response = adapter.query_binary_message(managed.resource, command, delay_s=delay_s)
            return QueryBinaryMessageResult(
                session_id=session_id,
                command=command,
                payload_mode=payload_mode,
                resource_name=managed.resource_name,
                delay_s=delay_s,
                response=_encode_binary_output(
                    session_id=session_id,
                    payload_mode=payload_mode,
                    payload=response,
                    registry=registry,
                    output_file_path=output_file_path,
                    output_file_conflict=output_file_conflict,
                ),
            )
        except Exception as exc:
            return QueryBinaryMessageResult(
                session_id=session_id,
                command=command,
                payload_mode=payload_mode,
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
