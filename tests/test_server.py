from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyvisa_mcp.config import ServerConfig
from pyvisa_mcp.resources import RESOURCE_URIS
from pyvisa_mcp.server import create_server
from pyvisa_mcp.tools import TOOL_NAMES


@unittest.skipUnless(importlib.util.find_spec("pyvisa_sim") is not None, "pyvisa-sim is not installed")
class ServerIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        profile = Path(__file__).resolve().parent / "fixtures" / "pyvisa_sim.yaml"
        self.backend = f"{profile.as_posix()}@sim"
        self.server = create_server(ServerConfig(default_backend=self.backend))

    async def test_create_server_registers_expected_tools_and_resources(self) -> None:
        tools = await self.server.list_tools()
        resources = await self.server.list_resources()

        self.assertEqual([tool.name for tool in tools], TOOL_NAMES)
        self.assertEqual([str(resource.uri) for resource in resources], RESOURCE_URIS)

    async def test_tool_schemas_include_parameter_descriptions(self) -> None:
        tools = await self.server.list_tools()
        tools_by_name = {tool.name: tool for tool in tools}

        open_schema = tools_by_name["open_resource_session"].inputSchema["properties"]
        query_schema = tools_by_name["query_message"].inputSchema["properties"]
        attribute_schema = tools_by_name["set_resource_attribute"].inputSchema["properties"]
        binary_write_schema = tools_by_name["write_binary_message"].inputSchema["properties"]

        self.assertIn("Fully qualified VISA resource name", open_schema["resource_name"]["description"])
        self.assertIn("Open timeout in milliseconds", open_schema["open_timeout_ms"]["description"])
        self.assertIn("query command expected to return a response", query_schema["command"]["description"])
        self.assertIn("Common runtime attributes", attribute_schema["attribute"]["description"])
        self.assertIn("Attribute value to set", attribute_schema["value"]["description"])
        self.assertIn("Binary payload transport mode", binary_write_schema["payload_mode"]["description"])

    async def test_tool_schemas_include_parameter_examples(self) -> None:
        tools = await self.server.list_tools()
        tools_by_name = {tool.name: tool for tool in tools}

        open_schema = tools_by_name["open_resource_session"].inputSchema["properties"]
        query_schema = tools_by_name["query_message"].inputSchema["properties"]
        attribute_schema = tools_by_name["set_resource_attribute"].inputSchema["properties"]
        binary_write_schema = tools_by_name["write_binary_message"].inputSchema["properties"]

        self.assertIn("ASRL2::INSTR", open_schema["resource_name"]["examples"])
        self.assertIn(5000, open_schema["open_timeout_ms"]["examples"])
        self.assertIn("*IDN?", query_schema["command"]["examples"])
        self.assertIn("timeout", attribute_schema["attribute"]["examples"])
        self.assertIn("3000", attribute_schema["value"]["examples"])
        self.assertIn("base64", binary_write_schema["payload_mode"]["examples"])

    async def test_tool_output_schemas_include_result_descriptions(self) -> None:
        tools = await self.server.list_tools()
        tools_by_name = {tool.name: tool for tool in tools}

        open_schema = tools_by_name["open_resource_session"].outputSchema
        query_schema = tools_by_name["query_message"].outputSchema
        binary_read_schema = tools_by_name["read_binary_message"].outputSchema

        self.assertIn("Resource name requested by the open operation", open_schema["properties"]["resource_name"]["description"])
        self.assertIn("Session details when the resource opens successfully", open_schema["properties"]["session"]["description"])
        self.assertIn("Structured error when the open operation fails", open_schema["properties"]["error"]["description"])
        self.assertIn("String response returned by the instrument", query_schema["properties"]["response"]["description"])
        self.assertIn("Machine-readable error code", query_schema["$defs"]["OperationError"]["properties"]["code"]["description"])
        self.assertIn("Binary payload returned by the read operation", binary_read_schema["properties"]["payload"]["description"])

    async def test_tool_output_schemas_include_result_examples(self) -> None:
        tools = await self.server.list_tools()
        tools_by_name = {tool.name: tool for tool in tools}

        open_schema = tools_by_name["open_resource_session"].outputSchema
        query_schema = tools_by_name["query_message"].outputSchema
        attribute_schema = tools_by_name["get_resource_attribute"].outputSchema
        binary_query_schema = tools_by_name["query_binary_message"].outputSchema

        self.assertIn("ASRL2::INSTR", open_schema["properties"]["resource_name"]["examples"])
        self.assertIn("12345678-1234-4123-8123-123456789abc", open_schema["$defs"]["SessionSummary"]["properties"]["session_id"]["examples"])
        self.assertIn("PYVISA-MCP,SIM,0.1\n", query_schema["properties"]["response"]["examples"])
        self.assertIn("unknown_session", query_schema["$defs"]["OperationError"]["properties"]["code"]["examples"])
        self.assertIn("timeout", attribute_schema["properties"]["attribute"]["examples"])
        self.assertIn("base64", binary_query_schema["properties"]["payload_mode"]["examples"])
        self.assertIn("AQID", binary_query_schema["$defs"]["BinaryPayloadReference"]["properties"]["data_base64"]["examples"])

    async def test_capability_and_backend_resources_match_server_contract(self) -> None:
        capability_payload = json.loads((await self.server.read_resource("pyvisa-mcp://capabilities"))[0].content)
        backend_content, backend_payload = await self.server.call_tool("get_backend_diagnostics", {})

        self.assertEqual(capability_payload["tool_count"], len(TOOL_NAMES))
        self.assertEqual(capability_payload["resource_count"], len(RESOURCE_URIS))
        self.assertEqual(capability_payload["tools"], TOOL_NAMES)
        self.assertEqual(capability_payload["resources"], RESOURCE_URIS)
        self.assertEqual(len(backend_content), 1)
        self.assertTrue(backend_payload["available"])
        self.assertEqual(backend_payload["backend_hint"], self.backend)

    async def test_server_session_flow_updates_session_resource(self) -> None:
        _, visible_payload = await self.server.call_tool("list_visible_resources", {"query": "?*"})
        _, open_payload = await self.server.call_tool(
            "open_resource_session",
            {"resource_name": "ASRL2::INSTR", "timeout_ms": 2500},
        )
        session_id = open_payload["session"]["session_id"]
        sessions_during = json.loads((await self.server.read_resource("pyvisa-mcp://sessions"))[0].content)
        _, query_payload = await self.server.call_tool(
            "query_message",
            {"session_id": session_id, "command": "*IDN?"},
        )
        _, close_payload = await self.server.call_tool(
            "close_resource_session",
            {"session_id": session_id},
        )
        sessions_after = json.loads((await self.server.read_resource("pyvisa-mcp://sessions"))[0].content)

        self.assertEqual(visible_payload["resource_count"], 1)
        self.assertEqual(visible_payload["resources"][0]["resource_name"], "ASRL2::INSTR")
        self.assertEqual(open_payload["resource_name"], "ASRL2::INSTR")
        self.assertEqual(open_payload["session"]["timeout_ms"], 2500)
        self.assertEqual(sessions_during["session_count"], 1)
        self.assertEqual(sessions_during["sessions"][0]["session_id"], session_id)
        self.assertEqual(query_payload["resource_name"], "ASRL2::INSTR")
        self.assertEqual(query_payload["response"], "PYVISA-MCP,SIM,0.1\n")
        self.assertTrue(close_payload["closed"])
        self.assertEqual(close_payload["resource_name"], "ASRL2::INSTR")
        self.assertEqual(sessions_after["session_count"], 0)


if __name__ == "__main__":
    unittest.main()