from __future__ import annotations

from contextlib import AsyncExitStack
from dataclasses import dataclass
import json
import os
import re
import shlex
import sys
from typing import Any, Protocol

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


_UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)

HELP_TEXT = """Commands:
  help
  json on|off
  tools
  resources
  backend|backend-status
  visible [query]
  capabilities
  sessions
  read-resource <uri>
  open <resource_name> [--open-timeout-ms N] [--timeout-ms N] [--read-termination VALUE] [--write-termination VALUE] [--query-delay-s F] [--chunk-size N]
  close [session_id|@]
  query [session_id|@] [--delay-s F] <command>
  read [session_id|@]
  write [session_id|@] <message>
    query-bin [session_id|@] [--payload-mode base64|temp_file] [--output-file PATH] [--output-conflict error|overwrite] [--delay-s F] <command>
    read-bin [session_id|@] [--payload-mode base64|temp_file] [--output-file PATH] [--output-conflict error|overwrite]
    write-bin [session_id|@] (--base64 DATA | --file PATH)
  info <resource_name>
  get-attr [session_id|@] <attribute>
  set-attr [session_id|@] <attribute> <value>
  exit|quit
"""


@dataclass(slots=True)
class CliSettings:
    python_executable: str = sys.executable
    server_module: str = "pyvisa_mcp.server"
    cwd: str | None = None
    backend: str | None = None
    default_query: str | None = None
    default_open_timeout_ms: int | None = None
    default_timeout_ms: int | None = None

    def to_server_parameters(self) -> StdioServerParameters:
        env = os.environ.copy()
        env["PYVISA_MCP_TRANSPORT"] = "stdio"
        if self.backend is not None:
            env["PYVISA_MCP_BACKEND"] = self.backend
        if self.default_query is not None:
            env["PYVISA_MCP_DEFAULT_QUERY"] = self.default_query
        if self.default_open_timeout_ms is not None:
            env["PYVISA_MCP_DEFAULT_OPEN_TIMEOUT_MS"] = str(self.default_open_timeout_ms)
        if self.default_timeout_ms is not None:
            env["PYVISA_MCP_DEFAULT_TIMEOUT_MS"] = str(self.default_timeout_ms)
        return StdioServerParameters(
            command=self.python_executable,
            args=["-m", self.server_module],
            env=env,
            cwd=self.cwd,
        )


@dataclass(slots=True)
class CommandResult:
    text: str = ""
    exit_requested: bool = False
    error: bool = False


class CliRuntimeProtocol(Protocol):
    async def list_tools(self) -> list[str]: ...

    async def list_resources(self) -> list[str]: ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...

    async def read_resource(self, uri: str) -> Any: ...


class CliRuntime:
    def __init__(self, settings: CliSettings) -> None:
        self._settings = settings
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None

    async def __aenter__(self) -> "CliRuntime":
        stack = AsyncExitStack()
        read_stream, write_stream = await stack.enter_async_context(
            stdio_client(self._settings.to_server_parameters())
        )
        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()
        self._stack = stack
        self._session = session
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._stack is not None:
            await self._stack.aclose()
        self._stack = None
        self._session = None

    @property
    def session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError("CLI runtime is not connected")
        return self._session

    async def list_tools(self) -> list[str]:
        result = await self.session.list_tools()
        return [tool.name for tool in result.tools]

    async def list_resources(self) -> list[str]:
        result = await self.session.list_resources()
        return [str(resource.uri) for resource in result.resources]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = await self.session.call_tool(name, arguments)
        structured_content = getattr(result, "structuredContent", None)
        if structured_content is not None:
            return dict(structured_content)

        text_fragments = [item.text for item in result.content if hasattr(item, "text")]
        if len(text_fragments) == 1:
            parsed = _try_json_load(text_fragments[0])
            if isinstance(parsed, dict):
                return parsed
            return {"content": parsed}
        return {"content": text_fragments}

    async def read_resource(self, uri: str) -> Any:
        result = await self.session.read_resource(uri)
        texts = [item.text for item in result.contents if hasattr(item, "text")]
        if len(texts) == 1:
            return _try_json_load(texts[0])
        return [_try_json_load(text) for text in texts]


class PyvisaMcpCli:
    def __init__(self, runtime: CliRuntimeProtocol, *, json_output: bool = False) -> None:
        self._runtime = runtime
        self._json_output = json_output
        self._last_session_id: str | None = None

    async def execute_line(self, line: str) -> CommandResult:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return CommandResult()

        try:
            tokens = shlex.split(stripped)
        except ValueError as exc:
            return CommandResult(text=f"Parse error: {exc}", error=True)

        command = tokens[0].lower()
        arguments = tokens[1:]

        try:
            if command == "help":
                return CommandResult(text=HELP_TEXT.strip())
            if command in {"exit", "quit"}:
                return CommandResult(exit_requested=True)
            if command == "json":
                return self._handle_json_toggle(arguments)
            if command == "tools":
                payload = await self._runtime.list_tools()
                return CommandResult(text=self._render_list("Tools", payload))
            if command == "resources":
                payload = await self._runtime.list_resources()
                return CommandResult(text=self._render_list("Resources", payload))
            if command in {"backend", "backend-status"}:
                payload = await self._runtime.call_tool("get_backend_diagnostics", {})
                return self._render_payload_result(command, payload)
            if command == "visible":
                tool_args = {} if not arguments else {"query": arguments[0]}
                payload = await self._runtime.call_tool("list_visible_resources", tool_args)
                return self._render_payload_result(command, payload)
            if command == "capabilities":
                payload = await self._runtime.read_resource("pyvisa-mcp://capabilities")
                return self._render_payload_result(command, payload)
            if command == "sessions":
                payload = await self._runtime.read_resource("pyvisa-mcp://sessions")
                return self._render_payload_result(command, payload)
            if command == "read-resource":
                if not arguments:
                    raise ValueError("read-resource requires <uri>")
                payload = await self._runtime.read_resource(arguments[0])
                return self._render_payload_result(command, payload)
            if command == "open":
                payload = await self._runtime.call_tool("open_resource_session", _parse_open_arguments(arguments))
                session = payload.get("session")
                if isinstance(session, dict):
                    self._last_session_id = session.get("session_id")
                return self._render_payload_result(command, payload)
            if command == "close":
                session_id, remaining = self._resolve_optional_session(arguments)
                if remaining:
                    raise ValueError("close only accepts an optional session identifier")
                payload = await self._runtime.call_tool(
                    "close_resource_session",
                    {"session_id": session_id},
                )
                if payload.get("closed") and session_id == self._last_session_id:
                    self._last_session_id = None
                return self._render_payload_result(command, payload)
            if command == "query":
                session_id, remaining = self._resolve_optional_session(arguments)
                tool_args = _parse_query_arguments(session_id, remaining)
                payload = await self._runtime.call_tool("query_message", tool_args)
                return self._render_payload_result(command, payload)
            if command == "read":
                session_id, remaining = self._resolve_optional_session(arguments)
                if remaining:
                    raise ValueError("read only accepts an optional session identifier")
                payload = await self._runtime.call_tool("read_message", {"session_id": session_id})
                return self._render_payload_result(command, payload)
            if command == "write":
                session_id, remaining = self._resolve_optional_session(arguments)
                if not remaining:
                    raise ValueError("write requires a message")
                payload = await self._runtime.call_tool(
                    "write_message",
                    {"session_id": session_id, "message": " ".join(remaining)},
                )
                return self._render_payload_result(command, payload)
            if command == "read-bin":
                session_id, remaining = self._resolve_optional_session(arguments)
                payload = await self._runtime.call_tool(
                    "read_binary_message",
                    _parse_binary_read_arguments(session_id, remaining),
                )
                return self._render_payload_result(command, payload)
            if command == "write-bin":
                session_id, remaining = self._resolve_optional_session(arguments)
                payload = await self._runtime.call_tool(
                    "write_binary_message",
                    _parse_binary_write_arguments(session_id, remaining),
                )
                return self._render_payload_result(command, payload)
            if command == "query-bin":
                session_id, remaining = self._resolve_optional_session(arguments)
                payload = await self._runtime.call_tool(
                    "query_binary_message",
                    _parse_binary_query_arguments(session_id, remaining),
                )
                return self._render_payload_result(command, payload)
            if command == "info":
                if not arguments:
                    raise ValueError("info requires <resource_name>")
                payload = await self._runtime.call_tool(
                    "inspect_resource_info",
                    {"resource_name": arguments[0]},
                )
                return self._render_payload_result(command, payload)
            if command == "get-attr":
                session_id, remaining = self._resolve_optional_session(arguments)
                if len(remaining) != 1:
                    raise ValueError("get-attr requires an attribute name")
                payload = await self._runtime.call_tool(
                    "get_resource_attribute",
                    {"session_id": session_id, "attribute": remaining[0]},
                )
                return self._render_payload_result(command, payload)
            if command == "set-attr":
                session_id, remaining = self._resolve_optional_session(arguments)
                if len(remaining) < 2:
                    raise ValueError("set-attr requires <attribute> <value>")
                payload = await self._runtime.call_tool(
                    "set_resource_attribute",
                    {
                        "session_id": session_id,
                        "attribute": remaining[0],
                        "value": " ".join(remaining[1:]),
                    },
                )
                return self._render_payload_result(command, payload)
        except ValueError as exc:
            return CommandResult(text=str(exc), error=True)

        return CommandResult(text=f"Unknown command: {command}", error=True)

    def _handle_json_toggle(self, arguments: list[str]) -> CommandResult:
        if len(arguments) != 1 or arguments[0] not in {"on", "off"}:
            return CommandResult(text="json requires 'on' or 'off'", error=True)
        self._json_output = arguments[0] == "on"
        state = "on" if self._json_output else "off"
        return CommandResult(text=f"JSON output {state}")

    def _resolve_optional_session(self, arguments: list[str]) -> tuple[str, list[str]]:
        if arguments and _looks_like_session_token(arguments[0]):
            session_id = self._resolve_session_token(arguments[0])
            return session_id, arguments[1:]
        session_id = self._resolve_session_token("@")
        return session_id, arguments

    def _resolve_session_token(self, token: str) -> str:
        if token == "@":
            if self._last_session_id is None:
                raise ValueError("No active session. Open a resource first or pass a session_id.")
            return self._last_session_id
        return token

    def _render_list(self, label: str, items: list[str]) -> str:
        if self._json_output:
            return _dump_json(items)
        if not items:
            return f"{label}: none"
        return "\n".join([f"{label}:"] + [f"- {item}" for item in items])

    def _render_payload_result(self, command: str, payload: Any) -> CommandResult:
        if self._json_output:
            return CommandResult(text=_dump_json(payload), error=_payload_has_error(payload))

        error = _extract_error(payload)
        if error is not None:
            code = error.get("code", "error")
            message = error.get("message", "Unknown error")
            return CommandResult(text=f"ERROR [{code}] {message}", error=True)

        if command in {"backend", "backend-status"}:
            available = payload.get("available")
            backend_hint = payload.get("backend_hint") or "default"
            return CommandResult(text=f"Backend ready: {available} ({backend_hint})")
        if command == "visible":
            resources = payload.get("resources", [])
            if not resources:
                return CommandResult(text="No visible resources")
            lines = ["Visible resources:"]
            for item in resources:
                lines.append(f"- {item['resource_name']}")
            return CommandResult(text="\n".join(lines))
        if command == "capabilities":
            return CommandResult(
                text=f"Capabilities: {payload.get('tool_count', 0)} tools, {payload.get('resource_count', 0)} resources"
            )
        if command == "sessions":
            sessions = payload.get("sessions", [])
            if not sessions:
                return CommandResult(text="No active sessions")
            lines = ["Sessions:"]
            for item in sessions:
                lines.append(f"- {item['session_id']} -> {item['resource_name']}")
            return CommandResult(text="\n".join(lines))
        if command == "read-resource":
            return CommandResult(text=_dump_json(payload))
        if command == "open":
            session = payload.get("session", {})
            return CommandResult(
                text=f"Opened session {session.get('session_id')} for {payload.get('resource_name')}"
            )
        if command == "close":
            return CommandResult(
                text=f"Closed session {payload.get('session_id')} for {payload.get('resource_name')}"
            )
        if command == "query":
            return CommandResult(text=str(payload.get("response", "")).rstrip("\n"))
        if command == "read":
            return CommandResult(text=str(payload.get("data", "")).rstrip("\n"))
        if command == "write":
            return CommandResult(
                text=f"Wrote {payload.get('bytes_written')} bytes to {payload.get('resource_name')}"
            )
        if command == "write-bin":
            return CommandResult(
                text=f"Wrote {payload.get('bytes_written')} binary bytes to {payload.get('resource_name')}"
            )
        if command == "read-bin":
            return CommandResult(text=_render_binary_payload_summary("Read", payload.get("payload")))
        if command == "query-bin":
            return CommandResult(text=_render_binary_payload_summary("Query returned", payload.get("response")))
        if command == "info":
            info = payload.get("info") or {}
            return CommandResult(
                text=f"{payload.get('resource_name')}: class={info.get('resource_class')} alias={info.get('alias')}"
            )
        if command in {"get-attr", "set-attr"}:
            return CommandResult(text=f"{payload.get('attribute')} = {payload.get('value')}")
        return CommandResult(text=_dump_json(payload))


def _parse_open_arguments(arguments: list[str]) -> dict[str, Any]:
    if not arguments:
        raise ValueError("open requires <resource_name>")

    tool_args: dict[str, Any] = {"resource_name": arguments[0]}
    index = 1
    option_types = {
        "--open-timeout-ms": ("open_timeout_ms", int),
        "--timeout-ms": ("timeout_ms", int),
        "--query-delay-s": ("query_delay_s", float),
        "--chunk-size": ("chunk_size", int),
        "--read-termination": ("read_termination", _decode_escapes),
        "--write-termination": ("write_termination", _decode_escapes),
    }

    while index < len(arguments):
        option = arguments[index]
        mapping = option_types.get(option)
        if mapping is None:
            raise ValueError(f"Unknown open option: {option}")
        if index + 1 >= len(arguments):
            raise ValueError(f"Missing value for {option}")
        key, caster = mapping
        tool_args[key] = caster(arguments[index + 1])
        index += 2

    return tool_args


def _parse_query_arguments(session_id: str, arguments: list[str]) -> dict[str, Any]:
    tool_args: dict[str, Any] = {"session_id": session_id}
    if not arguments:
        raise ValueError("query requires a command")

    index = 0
    while index < len(arguments):
        token = arguments[index]
        if token == "--delay-s":
            if index + 1 >= len(arguments):
                raise ValueError("Missing value for --delay-s")
            tool_args["delay_s"] = float(arguments[index + 1])
            index += 2
            continue
        tool_args["command"] = " ".join(arguments[index:])
        break

    if "command" not in tool_args:
        raise ValueError("query requires a command")
    return tool_args


def _parse_binary_read_arguments(session_id: str, arguments: list[str]) -> dict[str, Any]:
    tool_args: dict[str, Any] = {"session_id": session_id, "payload_mode": "base64"}
    index = 0
    while index < len(arguments):
        token = arguments[index]
        if token == "--payload-mode":
            if index + 1 >= len(arguments):
                raise ValueError("Missing value for --payload-mode")
            tool_args["payload_mode"] = _parse_binary_payload_mode(arguments[index + 1])
            index += 2
            continue
        if token == "--output-file":
            if index + 1 >= len(arguments):
                raise ValueError("Missing value for --output-file")
            tool_args["output_file_path"] = arguments[index + 1]
            index += 2
            continue
        if token == "--output-conflict":
            if index + 1 >= len(arguments):
                raise ValueError("Missing value for --output-conflict")
            tool_args["output_file_conflict"] = _parse_output_file_conflict(arguments[index + 1])
            index += 2
            continue
        raise ValueError("read-bin only accepts optional --payload-mode base64|temp_file, --output-file PATH, and --output-conflict error|overwrite")

    if "output_file_path" in tool_args and tool_args["payload_mode"] != "temp_file":
        raise ValueError("--output-file requires --payload-mode temp_file")
    if "output_file_conflict" in tool_args and "output_file_path" not in tool_args:
        raise ValueError("--output-conflict requires --output-file PATH")
    return tool_args


def _parse_binary_write_arguments(session_id: str, arguments: list[str]) -> dict[str, Any]:
    if len(arguments) != 2:
        raise ValueError("write-bin requires exactly one of --base64 DATA or --file PATH")
    option, value = arguments
    if option == "--base64":
        return {"session_id": session_id, "payload_mode": "base64", "data_base64": value}
    if option == "--file":
        return {"session_id": session_id, "payload_mode": "temp_file", "file_path": value}
    raise ValueError("write-bin requires --base64 DATA or --file PATH")


def _parse_binary_query_arguments(session_id: str, arguments: list[str]) -> dict[str, Any]:
    tool_args: dict[str, Any] = {"session_id": session_id, "payload_mode": "base64"}
    if not arguments:
        raise ValueError("query-bin requires a command")

    index = 0
    while index < len(arguments):
        token = arguments[index]
        if token == "--delay-s":
            if index + 1 >= len(arguments):
                raise ValueError("Missing value for --delay-s")
            tool_args["delay_s"] = float(arguments[index + 1])
            index += 2
            continue
        if token == "--payload-mode":
            if index + 1 >= len(arguments):
                raise ValueError("Missing value for --payload-mode")
            tool_args["payload_mode"] = _parse_binary_payload_mode(arguments[index + 1])
            index += 2
            continue
        if token == "--output-file":
            if index + 1 >= len(arguments):
                raise ValueError("Missing value for --output-file")
            tool_args["output_file_path"] = arguments[index + 1]
            index += 2
            continue
        if token == "--output-conflict":
            if index + 1 >= len(arguments):
                raise ValueError("Missing value for --output-conflict")
            tool_args["output_file_conflict"] = _parse_output_file_conflict(arguments[index + 1])
            index += 2
            continue
        tool_args["command"] = " ".join(arguments[index:])
        break

    if "command" not in tool_args:
        raise ValueError("query-bin requires a command")
    if "output_file_path" in tool_args and tool_args["payload_mode"] != "temp_file":
        raise ValueError("--output-file requires --payload-mode temp_file")
    if "output_file_conflict" in tool_args and "output_file_path" not in tool_args:
        raise ValueError("--output-conflict requires --output-file PATH")
    return tool_args


def _looks_like_session_token(token: str) -> bool:
    return token == "@" or bool(_UUID_PATTERN.match(token))


def _extract_error(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            return error
    return None


def _payload_has_error(payload: Any) -> bool:
    return _extract_error(payload) is not None


def _try_json_load(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _decode_escapes(value: str) -> str:
    return bytes(value, "utf-8").decode("unicode_escape")


def _parse_binary_payload_mode(value: str) -> str:
    if value not in {"base64", "temp_file"}:
        raise ValueError("payload mode must be 'base64' or 'temp_file'")
    return value


def _parse_output_file_conflict(value: str) -> str:
    if value not in {"error", "overwrite"}:
        raise ValueError("output conflict must be 'error' or 'overwrite'")
    return value


def _render_binary_payload_summary(prefix: str, payload: Any) -> str:
    if not isinstance(payload, dict):
        return f"{prefix}: no payload"
    byte_count = payload.get("byte_count")
    payload_mode = payload.get("payload_mode")
    if payload_mode == "temp_file":
        ownership = "auto-cleanup on close" if payload.get("cleanup_on_close") else "caller-managed file"
        return f"{prefix} {byte_count} bytes to {payload.get('file_path')} ({ownership})"
    data_base64 = str(payload.get("data_base64") or "")
    preview = data_base64 if len(data_base64) <= 48 else f"{data_base64[:45]}..."
    return f"{prefix} {byte_count} bytes as base64: {preview}"