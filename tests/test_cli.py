from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyvisa_mcp.cli_runtime import PyvisaMcpCli


class FakeRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, object]] = []

    async def list_tools(self) -> list[str]:
        self.calls.append(("list_tools", "", None))
        return ["list_visible_resources", "query_message"]

    async def list_resources(self) -> list[str]:
        self.calls.append(("list_resources", "", None))
        return ["pyvisa-mcp://sessions"]

    async def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        self.calls.append(("call_tool", name, dict(arguments)))
        if name == "open_resource_session":
            return {
                "resource_name": "ASRL2::INSTR",
                "session": {
                    "session_id": "11111111-1111-4111-8111-111111111111",
                    "resource_name": "ASRL2::INSTR",
                    "timeout_ms": 2500,
                },
                "error": None,
            }
        if name == "query_message":
            return {
                "session_id": str(arguments["session_id"]),
                "command": str(arguments["command"]),
                "resource_name": "ASRL2::INSTR",
                "response": "PYVISA-MCP,SIM,0.1\n",
                "error": None,
            }
        if name == "close_resource_session":
            return {
                "session_id": str(arguments["session_id"]),
                "closed": True,
                "resource_name": "ASRL2::INSTR",
                "error": None,
            }
        if name == "get_backend_diagnostics":
            return {
                "available": True,
                "backend_hint": "@sim",
                "error": None,
            }
        if name == "set_resource_attribute":
            return {
                "session_id": str(arguments["session_id"]),
                "attribute": str(arguments["attribute"]),
                "value": arguments["value"],
                "error": None,
            }
        raise AssertionError(f"Unexpected tool call: {name}")

    async def read_resource(self, uri: str):
        self.calls.append(("read_resource", uri, None))
        return {"session_count": 1, "sessions": [{"session_id": "11111111-1111-4111-8111-111111111111", "resource_name": "ASRL2::INSTR"}]}


class CliCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_open_query_and_close_reuse_last_session(self) -> None:
        cli = PyvisaMcpCli(FakeRuntime())

        opened = await cli.execute_line("open ASRL2::INSTR --timeout-ms 2500")
        queried = await cli.execute_line('query "*IDN?"')
        closed = await cli.execute_line("close")

        self.assertIn("Opened session 11111111-1111-4111-8111-111111111111", opened.text)
        self.assertEqual(queried.text, "PYVISA-MCP,SIM,0.1")
        self.assertIn("Closed session 11111111-1111-4111-8111-111111111111", closed.text)

    async def test_json_mode_and_resource_rendering(self) -> None:
        cli = PyvisaMcpCli(FakeRuntime())

        toggled = await cli.execute_line("json on")
        sessions = await cli.execute_line("sessions")

        self.assertEqual(toggled.text, "JSON output on")
        self.assertIn('"session_count": 1', sessions.text)

    async def test_missing_session_reports_clear_error(self) -> None:
        cli = PyvisaMcpCli(FakeRuntime())

        result = await cli.execute_line('query "*IDN?"')

        self.assertTrue(result.error)
        self.assertIn("No active session", result.text)


if __name__ == "__main__":
    unittest.main()