import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(os.path.realpath(os.path.curdir))
LICENSE_CHOICE = "{{ cookiecutter.open_source_license }}"
PROJECT_SLUG = "{{ cookiecutter.project_slug }}"


def run(cmd: str, check: bool = True) -> int:
    result = subprocess.run(cmd, shell=True, cwd=PROJECT_DIR)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode


def remove_file(relative_path: str) -> None:
    target = PROJECT_DIR / relative_path
    if target.exists():
        target.unlink()


def uv_available() -> bool:
    return subprocess.run("which uv", shell=True, capture_output=True).returncode == 0


# Remove license file for proprietary projects
if LICENSE_CHOICE == "Proprietary":
    remove_file("LICENSE")

# Initialise git
print("\n> Initialising git repository...")
run("git init")
run("git add -A")

# Install dependencies and pre-commit hooks
if uv_available():
    print("\n> Installing dependencies with uv...")
    run("uv sync")
    print("\n> Installing pre-commit hooks...")
    run("uv run pre-commit install")
    run("uv run pre-commit install --hook-type commit-msg")
else:
    print(
        "\nWARNING: uv not found. Install from https://docs.astral.sh/uv/ then run:\n"
        "  uv sync\n"
        "  uv run pre-commit install\n"
        "  uv run pre-commit install --hook-type commit-msg"
    )

print(
    f"""
{"=" * 60}
 Agent repository created: {PROJECT_SLUG}
{"=" * 60}

Next steps:
  1. cd {PROJECT_SLUG}
  2. cp .env.example .env
  3. Fill in API keys and GCP settings in .env
  4. make dev          # run the agent locally at http://localhost:8000
  5. make test         # run unit tests
  6. make setup-gcp    # one-time GCP bootstrap (when ready to deploy)
  7. make deploy-dev   # deploy to Agent Engine (dev)

See README.md and CLAUDE.md for full documentation.
"""
)
