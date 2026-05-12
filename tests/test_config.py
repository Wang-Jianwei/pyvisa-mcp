from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyvisa_mcp.config import ServerConfig


class ServerConfigTests(unittest.TestCase):
    def test_from_env_uses_default_values_when_unset(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = ServerConfig.from_env()
        self.assertEqual(config.server_name, "PyVISA MCP")
        self.assertEqual(config.preferred_transport, "stdio")
        self.assertEqual(config.default_resource_query, "?*::INSTR")
        self.assertEqual(config.default_open_timeout_ms, 0)
        self.assertEqual(config.default_timeout_ms, 2000)

    def test_backend_argument_adds_prefix(self) -> None:
        config = ServerConfig(default_backend="py")
        self.assertEqual(config.backend_argument, "@py")

    def test_backend_argument_keeps_existing_prefix(self) -> None:
        config = ServerConfig(default_backend="@sim")
        self.assertEqual(config.backend_argument, "@sim")

    def test_backend_argument_keeps_explicit_sim_profile_backend(self) -> None:
        config = ServerConfig(default_backend="tests/fixtures/pyvisa_sim.yaml@sim")
        self.assertEqual(config.backend_argument, "tests/fixtures/pyvisa_sim.yaml@sim")

    def test_from_env_reads_expected_fields(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PYVISA_MCP_SERVER_NAME": "Lab Server",
                "PYVISA_MCP_BACKEND": "sim",
                "PYVISA_MCP_TRANSPORT": "stdio",
                "PYVISA_MCP_DEFAULT_QUERY": "?*",
                "PYVISA_MCP_DEFAULT_OPEN_TIMEOUT_MS": "10",
                "PYVISA_MCP_DEFAULT_TIMEOUT_MS": "4000",
            },
            clear=False,
        ):
            config = ServerConfig.from_env()
        self.assertEqual(config.server_name, "Lab Server")
        self.assertEqual(config.default_backend, "sim")
        self.assertEqual(config.default_resource_query, "?*")
        self.assertEqual(config.default_open_timeout_ms, 10)
        self.assertEqual(config.default_timeout_ms, 4000)

    def test_from_env_falls_back_to_stdio_for_invalid_transport(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PYVISA_MCP_TRANSPORT": "http",
            },
            clear=False,
        ):
            config = ServerConfig.from_env()
        self.assertEqual(config.preferred_transport, "stdio")


if __name__ == "__main__":
    unittest.main()
