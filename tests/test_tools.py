from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyvisa_mcp.config import ServerConfig
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

    def list_visible_resources(self, query: str):
        self.last_list_query = query
        return {"query": query, "resources": ["TCPIP0::1::INSTR"]}

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

    def read_resource_info(self, resource_name: str):
        return {"resource_name": resource_name, "info": {"resource_class": "INSTR"}}

    def get_attribute(self, resource: DummyResource, attribute: str):  # pragma: no cover - not used here
        return getattr(resource, attribute)

    def set_attribute(self, resource: DummyResource, attribute: str, value: object) -> object:
        self.last_set_attribute = (attribute, value)
        setattr(resource, attribute, value)
        return getattr(resource, attribute)


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

        self.assertEqual(result["query"], "?*")
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
        self.assertEqual(query_result.response, "QUERY:*IDN?:delay=0.1")
        self.assertTrue(close_result.closed)
        self.assertEqual(len(self.adapter.closed_resources), 1)

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
        self.assertEqual(snapshot.sessions[0].timeout_ms, 3000)
        self.assertIsNone(snapshot.sessions[0].read_termination)
        self.assertEqual(snapshot.sessions[0].query_delay_s, 0.5)
        self.assertEqual(self.adapter.last_set_attribute, ("query_delay", 0.5))


if __name__ == "__main__":
    unittest.main()