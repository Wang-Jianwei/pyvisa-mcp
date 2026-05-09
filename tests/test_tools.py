from __future__ import annotations

from pathlib import Path
import tempfile
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyvisa_mcp.config import ServerConfig
from pyvisa_mcp.schemas import AttributeResult, ResourceInfoResult, VisibleResourcesResult
from pyvisa_mcp.session_registry import SessionRegistry
from pyvisa_mcp.tools import coerce_attribute_value, register_tools


class FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, name: str):
        def decorator(func: object) -> object:
            self.tools[name] = func
            return func

        return decorator


class DummyResource:
    def __init__(self) -> None:
        self.timeout = 0
        self.read_termination = None
        self.write_termination = None
        self.query_delay = 0.0
        self.chunk_size = 20480
        self.closed = False

    def close(self) -> None:
        self.closed = True


class DummyAdapter:
    def __init__(self) -> None:
        self.last_set_attribute: tuple[str, object] | None = None
        self.last_list_query: str | None = None
        self.last_open_request: dict[str, object] | None = None
        self.closed_resources: list[DummyResource] = []
        self.last_binary_write: bytes | None = None
        self.binary_reads: list[bytes] = [b"\x00\x01raw", b"\x10 query"]

    def list_visible_resources(self, query: str):
        self.last_list_query = query
        return VisibleResourcesResult(
            query=query,
            backend_hint="@sim",
            resource_count=1,
            resources=[],
        )

    def backend_status(self):  # pragma: no cover - not used here
        raise NotImplementedError

    def open_resource(self, **kwargs: object) -> DummyResource:
        self.last_open_request = kwargs
        return DummyResource()

    def close_resource(self, resource: DummyResource) -> None:
        resource.close()
        self.closed_resources.append(resource)

    def write_message(self, resource: DummyResource, message: str):  # pragma: no cover - not used here
        del resource
        return len(message)

    def read_message(self, resource: DummyResource):  # pragma: no cover - not used here
        del resource
        return "READ:OK"

    def query_message(self, resource: DummyResource, command: str, *, delay_s: float | None = None):  # pragma: no cover - not used here
        del resource
        if delay_s is None:
            return f"QUERY:{command}"
        return f"QUERY:{command}:delay={delay_s}"

    def write_binary_message(self, resource: DummyResource, payload: bytes):
        del resource
        self.last_binary_write = payload
        return len(payload)

    def read_binary_message(self, resource: DummyResource):
        del resource
        return self.binary_reads.pop(0)

    def query_binary_message(self, resource: DummyResource, command: str, *, delay_s: float | None = None):
        del resource, command, delay_s
        return self.binary_reads.pop(0)

    def read_resource_info(self, resource_name: str):
        return ResourceInfoResult(resource_name=resource_name)

    def get_attribute(self, resource: DummyResource, attribute: str):  # pragma: no cover - not used here
        return getattr(resource, attribute)

    def set_attribute(self, resource: DummyResource, attribute: str, value: object) -> object:
        self.last_set_attribute = (attribute, value)
        setattr(resource, attribute, value)
        return getattr(resource, attribute)


class FailingAdapter(DummyAdapter):
    def __init__(self, *, fail_open: bool = False, fail_query: bool = False) -> None:
        super().__init__()
        self.fail_open = fail_open
        self.fail_query = fail_query

    def open_resource(self, **kwargs: object) -> DummyResource:
        self.last_open_request = kwargs
        if self.fail_open:
            raise RuntimeError("open failed")
        return super().open_resource(**kwargs)

    def query_message(self, resource: DummyResource, command: str, *, delay_s: float | None = None):
        if self.fail_query:
            raise RuntimeError("query failed")
        return super().query_message(resource, command, delay_s=delay_s)


class ToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mcp = FakeMCP()
        self.adapter = DummyAdapter()
        self.registry = SessionRegistry()
        self.config = ServerConfig()
        register_tools(self.mcp, adapter=self.adapter, registry=self.registry, config=self.config)

    def test_coerce_attribute_value_handles_common_runtime_settings(self) -> None:
        self.assertEqual(coerce_attribute_value("timeout", "2500"), 2500)
        self.assertEqual(coerce_attribute_value("query_delay", "0.25"), 0.25)
        self.assertEqual(coerce_attribute_value("chunk_size", 4096), 4096)
        self.assertIsNone(coerce_attribute_value("read_termination", "none"))
        self.assertIsNone(coerce_attribute_value("timeout", None))

    def test_coerce_attribute_value_rejects_invalid_chunk_size_null(self) -> None:
        with self.assertRaises(ValueError):
            coerce_attribute_value("chunk_size", None)

    def test_list_visible_resources_tool_passes_query(self) -> None:
        list_visible_resources = self.mcp.tools["list_visible_resources"]

        result = list_visible_resources("?*")

        self.assertEqual(result.query, "?*")
        self.assertEqual(result.backend_hint, "@sim")
        self.assertEqual(result.resource_count, 1)
        self.assertEqual(self.adapter.last_list_query, "?*")

    def test_open_query_and_close_resource_session_flow(self) -> None:
        open_resource_session = self.mcp.tools["open_resource_session"]
        query_message = self.mcp.tools["query_message"]
        close_resource_session = self.mcp.tools["close_resource_session"]

        open_result = open_resource_session(
            "TCPIP0::1::INSTR",
            open_timeout_ms=10,
            timeout_ms=3000,
            read_termination="\n",
        )
        session_id = open_result.session.session_id
        query_result = query_message(session_id, "*IDN?", delay_s=0.1)
        close_result = close_resource_session(session_id)

        self.assertEqual(self.adapter.last_open_request["resource_name"], "TCPIP0::1::INSTR")
        self.assertEqual(self.adapter.last_open_request["open_timeout_ms"], 10)
        self.assertEqual(open_result.resource_name, "TCPIP0::1::INSTR")
        self.assertEqual(query_result.response, "QUERY:*IDN?:delay=0.1")
        self.assertEqual(query_result.resource_name, "TCPIP0::1::INSTR")
        self.assertEqual(query_result.delay_s, 0.1)
        self.assertTrue(close_result.closed)
        self.assertEqual(close_result.resource_name, "TCPIP0::1::INSTR")
        self.assertEqual(len(self.adapter.closed_resources), 1)

    def test_open_resource_session_returns_structured_error_on_adapter_failure(self) -> None:
        mcp = FakeMCP()
        adapter = FailingAdapter(fail_open=True)
        registry = SessionRegistry()
        register_tools(mcp, adapter=adapter, registry=registry, config=self.config)

        open_resource_session = mcp.tools["open_resource_session"]
        result = open_resource_session("TCPIP0::1::INSTR")

        self.assertEqual(result.resource_name, "TCPIP0::1::INSTR")
        self.assertIsNone(result.session)
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "RuntimeError")
        self.assertEqual(result.error.message, "open failed")

    def test_query_message_returns_structured_error_for_unknown_session(self) -> None:
        query_message = self.mcp.tools["query_message"]

        result = query_message("missing-session", "*IDN?")

        self.assertIsNone(result.response)
        self.assertEqual(result.delay_s, None)
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "UnknownSessionError")

    def test_query_message_returns_structured_error_on_adapter_failure(self) -> None:
        mcp = FakeMCP()
        adapter = FailingAdapter(fail_query=True)
        registry = SessionRegistry()
        register_tools(mcp, adapter=adapter, registry=registry, config=self.config)
        session = registry.open(resource_name="TCPIP0::1::INSTR", resource=DummyResource())

        query_message = mcp.tools["query_message"]
        result = query_message(session.session_id, "*IDN?")

        self.assertIsNone(result.response)
        self.assertEqual(result.resource_name, None)
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "RuntimeError")
        self.assertEqual(result.error.message, "query failed")

    def test_close_resource_session_returns_unknown_session_error_code(self) -> None:
        close_resource_session = self.mcp.tools["close_resource_session"]

        result = close_resource_session("missing-session")

        self.assertFalse(result.closed)
        self.assertIsNone(result.resource_name)
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "unknown_session")

    def test_set_resource_attribute_updates_registry_with_typed_values(self) -> None:
        resource = DummyResource()
        session = self.registry.open(resource_name="TCPIP0::1::INSTR", resource=resource)

        set_resource_attribute = self.mcp.tools["set_resource_attribute"]
        timeout_result = set_resource_attribute(session.session_id, "timeout", "3000")
        read_term_result = set_resource_attribute(session.session_id, "read_termination", None)
        delay_result = set_resource_attribute(session.session_id, "query_delay", "0.5")

        snapshot = self.registry.list_summaries()
        self.assertEqual(timeout_result.value, 3000)
        self.assertIsNone(read_term_result.value)
        self.assertEqual(delay_result.value, 0.5)
        self.assertEqual(delay_result.resource_name, "TCPIP0::1::INSTR")
        self.assertEqual(snapshot.sessions[0].timeout_ms, 3000)
        self.assertIsNone(snapshot.sessions[0].read_termination)
        self.assertEqual(snapshot.sessions[0].query_delay_s, 0.5)
        self.assertEqual(self.adapter.last_set_attribute, ("query_delay", 0.5))

    def test_write_binary_message_accepts_base64_input(self) -> None:
        open_resource_session = self.mcp.tools["open_resource_session"]
        write_binary_message = self.mcp.tools["write_binary_message"]

        open_result = open_resource_session("TCPIP0::1::INSTR")
        session_id = open_result.session.session_id
        result = write_binary_message(session_id, payload_mode="base64", data_base64="AQID")

        self.assertEqual(result.bytes_written, 3)
        self.assertEqual(result.payload_mode, "base64")
        self.assertEqual(self.adapter.last_binary_write, b"\x01\x02\x03")

    def test_write_binary_message_accepts_file_input(self) -> None:
        open_resource_session = self.mcp.tools["open_resource_session"]
        write_binary_message = self.mcp.tools["write_binary_message"]

        open_result = open_resource_session("TCPIP0::1::INSTR")
        session_id = open_result.session.session_id
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            handle.write(b"\xaa\xbb")
            temp_path = handle.name

        try:
            result = write_binary_message(session_id, payload_mode="temp_file", file_path=temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

        self.assertEqual(result.bytes_written, 2)
        self.assertEqual(result.payload_mode, "temp_file")
        self.assertEqual(self.adapter.last_binary_write, b"\xaa\xbb")

    def test_read_binary_message_supports_base64_and_temp_file_modes(self) -> None:
        open_resource_session = self.mcp.tools["open_resource_session"]
        read_binary_message = self.mcp.tools["read_binary_message"]
        close_resource_session = self.mcp.tools["close_resource_session"]

        open_result = open_resource_session("TCPIP0::1::INSTR")
        session_id = open_result.session.session_id
        base64_result = read_binary_message(session_id, payload_mode="base64")
        temp_file_result = read_binary_message(session_id, payload_mode="temp_file")
        temp_path = Path(temp_file_result.payload.file_path)

        self.assertEqual(base64_result.payload.data_base64, "AAFyYXc=")
        self.assertEqual(temp_file_result.payload.payload_mode, "temp_file")
        self.assertTrue(temp_path.exists())
        self.assertEqual(temp_path.read_bytes(), b"\x10 query")

        close_resource_session(session_id)
        self.assertFalse(temp_path.exists())

    def test_read_binary_message_supports_explicit_output_file_without_auto_cleanup(self) -> None:
        open_resource_session = self.mcp.tools["open_resource_session"]
        read_binary_message = self.mcp.tools["read_binary_message"]
        close_resource_session = self.mcp.tools["close_resource_session"]

        self.adapter.binary_reads = [b"\xaa\xbb\xcc"]
        open_result = open_resource_session("TCPIP0::1::INSTR")
        session_id = open_result.session.session_id
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "capture.bin"

            result = read_binary_message(session_id, payload_mode="temp_file", output_file_path=str(output_path))
            close_resource_session(session_id)

            self.assertEqual(result.payload.file_path, str(output_path))
            self.assertFalse(result.payload.cleanup_on_close)
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_bytes(), b"\xaa\xbb\xcc")

    def test_query_binary_message_rejects_output_file_without_temp_file_mode(self) -> None:
        open_resource_session = self.mcp.tools["open_resource_session"]
        query_binary_message = self.mcp.tools["query_binary_message"]

        open_result = open_resource_session("TCPIP0::1::INSTR")
        session_id = open_result.session.session_id
        result = query_binary_message(session_id, "CURV?", payload_mode="base64", output_file_path="D:/captures/out.bin")

        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "ValueError")
        self.assertEqual(result.error.message, "output_file_path requires payload_mode temp_file")

    def test_read_binary_message_rejects_existing_output_file_by_default(self) -> None:
        open_resource_session = self.mcp.tools["open_resource_session"]
        read_binary_message = self.mcp.tools["read_binary_message"]

        self.adapter.binary_reads = [b"new-bytes"]
        open_result = open_resource_session("TCPIP0::1::INSTR")
        session_id = open_result.session.session_id
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "capture.bin"
            output_path.write_bytes(b"existing")

            result = read_binary_message(session_id, payload_mode="temp_file", output_file_path=str(output_path))

            self.assertIsNotNone(result.error)
            self.assertEqual(result.error.code, "FileExistsError")
            self.assertEqual(output_path.read_bytes(), b"existing")

    def test_query_binary_message_can_overwrite_existing_output_file_when_requested(self) -> None:
        open_resource_session = self.mcp.tools["open_resource_session"]
        query_binary_message = self.mcp.tools["query_binary_message"]

        self.adapter.binary_reads = [b"replacement"]
        open_result = open_resource_session("TCPIP0::1::INSTR")
        session_id = open_result.session.session_id
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "capture.bin"
            output_path.write_bytes(b"existing")

            result = query_binary_message(
                session_id,
                "CURV?",
                payload_mode="temp_file",
                output_file_path=str(output_path),
                output_file_conflict="overwrite",
            )

            self.assertIsNone(result.error)
            self.assertEqual(result.response.file_path, str(output_path))
            self.assertFalse(result.response.cleanup_on_close)
            self.assertEqual(output_path.read_bytes(), b"replacement")

    def test_query_binary_message_returns_structured_payload(self) -> None:
        open_resource_session = self.mcp.tools["open_resource_session"]
        query_binary_message = self.mcp.tools["query_binary_message"]

        open_result = open_resource_session("TCPIP0::1::INSTR")
        session_id = open_result.session.session_id
        result = query_binary_message(session_id, "CURV?", payload_mode="base64", delay_s=0.2)

        self.assertEqual(result.command, "CURV?")
        self.assertEqual(result.payload_mode, "base64")
        self.assertEqual(result.delay_s, 0.2)
        self.assertEqual(result.response.data_base64, "AAFyYXc=")
        self.assertIsNone(result.response.cleanup_on_close)


if __name__ == "__main__":
    unittest.main()