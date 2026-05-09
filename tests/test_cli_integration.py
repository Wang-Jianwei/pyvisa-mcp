from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliIntegrationTests(unittest.TestCase):
    def test_cli_backend_command_returns_json_payload(self) -> None:
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        src_path = str(root / "src")
        env["PYTHONPATH"] = src_path if not existing_pythonpath else os.pathsep.join([src_path, existing_pythonpath])

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyvisa_mcp.cli",
                "--json",
                "--no-prompt",
            ],
            input="backend\nexit\n",
            capture_output=True,
            text=True,
            cwd=root,
            env=env,
            check=False,
            timeout=20,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"available":', completed.stdout)
        self.assertIn('"resource_manager_ready":', completed.stdout)

    @unittest.skipUnless(importlib.util.find_spec("pyvisa_sim") is not None, "pyvisa-sim is not installed")
    def test_cli_repl_can_drive_sim_backend_from_piped_input(self) -> None:
        root = Path(__file__).resolve().parents[1]
        profile = Path(__file__).resolve().parent / "fixtures" / "pyvisa_sim.yaml"
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        src_path = str(root / "src")
        env["PYTHONPATH"] = src_path if not existing_pythonpath else os.pathsep.join([src_path, existing_pythonpath])

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyvisa_mcp.cli",
                "--backend",
                f"{profile.as_posix()}@sim",
                "--json",
                "--no-prompt",
            ],
            input="visible ?*\nopen ASRL2::INSTR --timeout-ms 2500\nquery \"*IDN?\"\nclose\nexit\n",
            capture_output=True,
            text=True,
            cwd=root,
            env=env,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"resource_name": "ASRL2::INSTR"', completed.stdout)
        self.assertIn('"response": "PYVISA-MCP,SIM,0.1\\n"', completed.stdout)
        self.assertIn('"closed": true', completed.stdout)

    @unittest.skipUnless(importlib.util.find_spec("pyvisa_sim") is not None, "pyvisa-sim is not installed")
    def test_cli_repl_can_query_binary_payload_from_sim_backend(self) -> None:
        root = Path(__file__).resolve().parents[1]
        profile = Path(__file__).resolve().parent / "fixtures" / "pyvisa_sim.yaml"
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        src_path = str(root / "src")
        env["PYTHONPATH"] = src_path if not existing_pythonpath else os.pathsep.join([src_path, existing_pythonpath])

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyvisa_mcp.cli",
                "--backend",
                f"{profile.as_posix()}@sim",
                "--json",
                "--no-prompt",
            ],
            input="open ASRL2::INSTR\nquery-bin CURV?\nclose\nexit\n",
            capture_output=True,
            text=True,
            cwd=root,
            env=env,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"payload_mode": "base64"', completed.stdout)
        self.assertIn('"data_base64": "w6nkuK0K"', completed.stdout)

    @unittest.skipUnless(importlib.util.find_spec("pyvisa_sim") is not None, "pyvisa-sim is not installed")
    def test_cli_repl_can_write_binary_query_to_explicit_file(self) -> None:
        root = Path(__file__).resolve().parents[1]
        profile = Path(__file__).resolve().parent / "fixtures" / "pyvisa_sim.yaml"
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        src_path = str(root / "src")
        env["PYTHONPATH"] = src_path if not existing_pythonpath else os.pathsep.join([src_path, existing_pythonpath])

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "query.bin"
            output_path.write_bytes(b"old")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pyvisa_mcp.cli",
                    "--backend",
                    f"{profile.as_posix()}@sim",
                    "--json",
                    "--no-prompt",
                ],
                input=f"open ASRL2::INSTR\nquery-bin --payload-mode temp_file --output-file {output_path.as_posix()} --output-conflict overwrite CURV?\nclose\nexit\n",
                capture_output=True,
                text=True,
                cwd=root,
                env=env,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('"cleanup_on_close": false', completed.stdout)
            self.assertIn('"payload_mode": "temp_file"', completed.stdout)
            self.assertIn('query.bin', completed.stdout)
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_bytes(), "é中\n".encode("utf-8"))

    @unittest.skipUnless(importlib.util.find_spec("pyvisa_sim") is not None, "pyvisa-sim is not installed")
    def test_cli_repl_reports_existing_output_file_without_overwrite(self) -> None:
        root = Path(__file__).resolve().parents[1]
        profile = Path(__file__).resolve().parent / "fixtures" / "pyvisa_sim.yaml"
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        src_path = str(root / "src")
        env["PYTHONPATH"] = src_path if not existing_pythonpath else os.pathsep.join([src_path, existing_pythonpath])

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "query.bin"
            output_path.write_bytes(b"old")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pyvisa_mcp.cli",
                    "--backend",
                    f"{profile.as_posix()}@sim",
                    "--json",
                    "--no-prompt",
                ],
                input=f"open ASRL2::INSTR\nquery-bin --payload-mode temp_file --output-file {output_path.as_posix()} CURV?\nclose\nexit\n",
                capture_output=True,
                text=True,
                cwd=root,
                env=env,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('"code": "FileExistsError"', completed.stderr)
            self.assertIn('"message": "Output file already exists:', completed.stderr)
            self.assertEqual(output_path.read_bytes(), b"old")


if __name__ == "__main__":
    unittest.main()