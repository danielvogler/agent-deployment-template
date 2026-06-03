#!/usr/bin/env python3
"""Local evaluation runner with human-readable output.

Usage:
    uv run python tests/evals/run_eval.py

This is a convenience wrapper around `make eval` (npx promptfoo).
Use it for quick local runs without needing Node.js promptfoo output parsing.
"""
import subprocess
import sys
from pathlib import Path

CONFIG = Path(__file__).parent / "promptfoo.yaml"


def main() -> None:
    print("Running promptfoo evaluation...")
    print(f"Config: {CONFIG}\n")

    result = subprocess.run(
        ["npx", "--yes", "promptfoo@latest", "eval", "--config", str(CONFIG)],
        capture_output=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
