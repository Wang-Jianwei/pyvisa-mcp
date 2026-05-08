from __future__ import annotations

import argparse
import os
import sys

import anyio

from .cli_runtime import CliRuntime, CliSettings, CommandResult, PyvisaMcpCli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive CLI for the local PyVISA MCP server")
    parser.add_argument("--backend", help="PyVISA backend, for example @sim or path/to/profile.yaml@sim")
    parser.add_argument("--default-query", help="Override the server default resource query")
    parser.add_argument("--open-timeout-ms", type=int, help="Override the server default open timeout")
    parser.add_argument("--timeout-ms", type=int, help="Override the server default session timeout")
    parser.add_argument("--json", action="store_true", help="Start with JSON output enabled")
    parser.add_argument("--no-prompt", action="store_true", help="Suppress the interactive prompt")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return anyio.run(_run_cli, args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"CLI startup failed: {exc}", file=sys.stderr)
        return 1


async def _run_cli(args: argparse.Namespace) -> int:
    settings = CliSettings(
        python_executable=sys.executable,
        cwd=os.getcwd(),
        backend=args.backend,
        default_query=args.default_query,
        default_open_timeout_ms=args.open_timeout_ms,
        default_timeout_ms=args.timeout_ms,
    )

    async with CliRuntime(settings) as runtime:
        cli = PyvisaMcpCli(runtime, json_output=args.json)
        prompt = "" if args.no_prompt else "pyvisa-mcp> "

        while True:
            try:
                line = await anyio.to_thread.run_sync(input, prompt)
            except EOFError:
                return 0

            result = await cli.execute_line(line)
            exit_code = _emit_result(result)
            if result.exit_requested:
                return exit_code


def _emit_result(result: CommandResult) -> int:
    if result.text:
        stream = sys.stderr if result.error else sys.stdout
        print(result.text, file=stream)
    if result.exit_requested:
        return 0
    return 1 if result.error else 0


if __name__ == "__main__":
    raise SystemExit(main())