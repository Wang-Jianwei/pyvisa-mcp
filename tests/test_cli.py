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
        if name == "read_binary_values":
            return {
                "session_id": str(arguments["session_id"]),
                "resource_name": "ASRL2::INSTR",
                "payload": {
                    "data_type": str(arguments.get("data_type", "f")),
                    "is_big_endian": bool(arguments.get("is_big_endian", False)),
                    "header_format": str(arguments.get("header_format", "ieee")),
                    "expect_termination": bool(arguments.get("expect_termination", True)),
                    "value_count": 3,
                    "values": [1.0, 2.5, 3.75],
                },
                "error": None,
            }
        if name == "query_binary_values":
            return {
                "session_id": str(arguments["session_id"]),
                "command": str(arguments["command"]),
                "resource_name": "ASRL2::INSTR",
                "delay_s": arguments.get("delay_s"),
                "payload": {
                    "data_type": str(arguments.get("data_type", "f")),
                    "is_big_endian": bool(arguments.get("is_big_endian", False)),
                    "header_format": str(arguments.get("header_format", "ieee")),
                    "expect_termination": bool(arguments.get("expect_termination", True)),
                    "value_count": 3,
                    "values": [1.0, 2.5, 3.75],
                },
                "error": None,
            }
        if name == "read_binary_message":
            file_path = arguments.get("output_file_path")
            return {
                "session_id": str(arguments["session_id"]),
                "resource_name": "ASRL2::INSTR",
                "payload": {
                    "payload_mode": str(arguments.get("payload_mode", "base64")),
                    "byte_count": 3,
                    "content_type": "application/octet-stream",
                    "data_base64": "AQID" if arguments.get("payload_mode", "base64") == "base64" else None,
                    "file_path": str(file_path) if file_path else ("C:/Temp/pyvisa-mcp/test.bin" if arguments.get("payload_mode") == "temp_file" else None),
                    "cleanup_on_close": False if file_path else (True if arguments.get("payload_mode") == "temp_file" else None),
                },
                "error": None,
            }
        if name == "query_binary_message":
            file_path = arguments.get("output_file_path")
            return {
                "session_id": str(arguments["session_id"]),
                "command": str(arguments["command"]),
                "payload_mode": str(arguments.get("payload_mode", "base64")),
                "resource_name": "ASRL2::INSTR",
                "delay_s": arguments.get("delay_s"),
                "response": {
                    "payload_mode": str(arguments.get("payload_mode", "base64")),
                    "byte_count": 3,
                    "content_type": "application/octet-stream",
                    "data_base64": "AQID" if arguments.get("payload_mode", "base64") == "base64" else None,
                    "file_path": str(file_path) if file_path else ("C:/Temp/pyvisa-mcp/query.bin" if arguments.get("payload_mode") == "temp_file" else None),
                    "cleanup_on_close": False if file_path else (True if arguments.get("payload_mode") == "temp_file" else None),
                },
                "error": None,
            }
        if name == "write_binary_message":
            return {
                "session_id": str(arguments["session_id"]),
                "payload_mode": str(arguments.get("payload_mode", "base64")),
                "resource_name": "ASRL2::INSTR",
                "bytes_written": 3,
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

    async def test_binary_commands_render_base64_and_temp_file_results(self) -> None:
        runtime = FakeRuntime()
        cli = PyvisaMcpCli(runtime)

        await cli.execute_line("open ASRL2::INSTR")
        write_result = await cli.execute_line("write-bin --base64 AQID")
        read_result = await cli.execute_line("read-bin")
        query_result = await cli.execute_line("query-bin --payload-mode temp_file CURV?")
        read_to_file_result = await cli.execute_line("read-bin --payload-mode temp_file --output-file D:/captures/read.bin")

        self.assertEqual(write_result.text, "Wrote 3 binary bytes to ASRL2::INSTR")
        self.assertIn("Read 3 bytes as base64: AQID", read_result.text)
        self.assertIn("Query returned 3 bytes to C:/Temp/pyvisa-mcp/query.bin (auto-cleanup on close)", query_result.text)
        self.assertIn("Read 3 bytes to D:/captures/read.bin (caller-managed file)", read_to_file_result.text)
        self.assertIn(("call_tool", "read_binary_message", {"session_id": "11111111-1111-4111-8111-111111111111", "payload_mode": "temp_file", "output_file_path": "D:/captures/read.bin"}), runtime.calls)

    async def test_binary_commands_reject_output_file_without_temp_file_mode(self) -> None:
        cli = PyvisaMcpCli(FakeRuntime())

        await cli.execute_line("open ASRL2::INSTR")
        result = await cli.execute_line("query-bin --output-file D:/captures/out.bin CURV?")

        self.assertTrue(result.error)
        self.assertIn("--output-file requires --payload-mode temp_file", result.text)

    async def test_binary_commands_reject_output_conflict_without_output_file(self) -> None:
        cli = PyvisaMcpCli(FakeRuntime())

        await cli.execute_line("open ASRL2::INSTR")
        result = await cli.execute_line("read-bin --payload-mode temp_file --output-conflict overwrite")

        self.assertTrue(result.error)
        self.assertIn("--output-conflict requires --output-file PATH", result.text)

    async def test_binary_values_commands_render_and_forward_arguments(self) -> None:
        runtime = FakeRuntime()
        cli = PyvisaMcpCli(runtime)

        await cli.execute_line("open ASRL2::INSTR")
        read_result = await cli.execute_line("read-values --datatype d --header-format hp --big-endian --expect-termination false")
        query_result = await cli.execute_line("query-values --datatype f --delay-s 0.25 WAV:DATA?")

        self.assertIn("Read 3 values (d): 1.0, 2.5, 3.75", read_result.text)
        self.assertIn("Query returned 3 values (f): 1.0, 2.5, 3.75", query_result.text)
        self.assertIn(
            (
                "call_tool",
                "read_binary_values",
                {
                    "session_id": "11111111-1111-4111-8111-111111111111",
                    "data_type": "d",
                    "header_format": "hp",
                    "is_big_endian": True,
                    "expect_termination": False,
                },
            ),
            runtime.calls,
        )
        self.assertIn(
            (
                "call_tool",
                "query_binary_values",
                {
                    "session_id": "11111111-1111-4111-8111-111111111111",
                    "data_type": "f",
                    "header_format": "ieee",
                    "is_big_endian": False,
                    "expect_termination": True,
                    "delay_s": 0.25,
                    "command": "WAV:DATA?",
                },
            ),
            runtime.calls,
        )

    async def test_binary_values_commands_reject_invalid_bool_literal(self) -> None:
        cli = PyvisaMcpCli(FakeRuntime())

        await cli.execute_line("open ASRL2::INSTR")
        result = await cli.execute_line("read-values --expect-termination maybe")

        self.assertTrue(result.error)
        self.assertIn("--expect-termination must be 'true' or 'false'", result.text)

    async def test_binary_commands_forward_output_conflict_policy(self) -> None:
        runtime = FakeRuntime()
        cli = PyvisaMcpCli(runtime)

        await cli.execute_line("open ASRL2::INSTR")
        await cli.execute_line("query-bin --payload-mode temp_file --output-file D:/captures/read.bin --output-conflict overwrite CURV?")

        self.assertIn(
            (
                "call_tool",
                "query_binary_message",
                {
                    "session_id": "11111111-1111-4111-8111-111111111111",
                    "payload_mode": "temp_file",
                    "output_file_path": "D:/captures/read.bin",
                    "output_file_conflict": "overwrite",
                    "command": "CURV?",
                },
            ),
            runtime.calls,
        )


if __name__ == "__main__":
    unittest.main()