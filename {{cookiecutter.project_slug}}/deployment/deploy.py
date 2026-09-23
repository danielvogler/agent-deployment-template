#!/usr/bin/env python3
"""Deploy the agent to Vertex AI Agent Engine.

Usage:
    uv run python deployment/deploy.py --env dev
    uv run python deployment/deploy.py --env prod
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from google.cloud.aiplatform_v1.types import SecretRef

# Ensure the project root is on the path when run as a script
# (python deployment/deploy.py puts deployment/ on sys.path, not the root).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def locked_requirements() -> list[str]:
    """Exact pins for every runtime dependency, exported from uv.lock.

    The container must install the versions the agent is pickled against here, not
    whatever newest release satisfies a version floor: an agent pickled under one
    google-adk and unpickled under another fails on every request, and a cloudpickle
    mismatch fails at container start. `uv run` syncs the environment to the lock
    first, so the lock is exactly what this process has imported.
    """
    try:
        result = subprocess.run(
            [
                "uv",
                "export",
                "--frozen",
                "--no-dev",
                "--no-emit-project",
                "--no-hashes",
                "--no-header",
                "--no-annotate",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", None) or exc
        raise RuntimeError(
            f"Could not export pinned requirements from uv.lock: {detail}"
        ) from exc
    return [line for line in result.stdout.splitlines() if line.strip()]


def deploy(env: str) -> None:
    import vertexai
    from vertexai import agent_engines

    from agent.agent import root_agent
    from deployment.config import DeploymentConfig

    config = DeploymentConfig.from_env()
    requirements = locked_requirements()

    logger.info("Deploying [%s] to Vertex AI Agent Engine", env)
    logger.info("  Project:  %s", config.project)
    logger.info("  Location: %s", config.location)
    logger.info("  Bucket:   %s", config.staging_bucket)
    logger.info("  Runtime SA: %s", config.service_account)

    vertexai.init(
        project=config.project,
        location=config.location,
        staging_bucket=config.staging_bucket,
    )

    # The pickled agent references agent.tools.* by module path, so the package has
    # to ship alongside it; prompts travels too, for runtime reads.
    extra_packages = ["agent", "prompts"]

    # dict value types are invariant, so dict[str, str] will not satisfy the SDK's
    # Dict[str, str | SecretRef]. Cast rather than widen, to keep config.py SDK-free.
    env_vars = cast("dict[str, str | SecretRef]", config.runtime_env_vars)

    # service_account is sent on create and update alike; omitting it falls back to
    # the shared service agent. See "Runtime identity" in AGENTS.md.
    if config.resource_name:
        logger.info("  Updating: %s", config.resource_name)
        existing = agent_engines.get(config.resource_name)
        remote_agent = existing.update(
            agent_engine=root_agent,
            requirements=requirements,
            extra_packages=extra_packages,
            gcs_dir_name=config.gcs_dir_name,
            env_vars=env_vars,
            service_account=config.service_account,
        )
    else:
        logger.info("  Creating new Agent Engine resource...")
        remote_agent = agent_engines.create(
            agent_engine=root_agent,
            requirements=requirements,
            display_name=config.agent_display_name,
            gcs_dir_name=config.gcs_dir_name,
            extra_packages=extra_packages,
            env_vars=env_vars,
            service_account=config.service_account,
        )

    resource_name = remote_agent.resource_name
    logger.info("Deployed: %s", resource_name)

    Path(".agent_engine_resource").write_text(resource_name + "\n")

    from deployment.scripts.health_check import run_smoke_test

    logger.info("Running smoke test...")
    if not run_smoke_test(remote_agent):
        sys.exit(1)

    # Emit for CI capture
    logger.info("AGENT_ENGINE_RESOURCE_NAME=%s", resource_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deploy agent to Vertex AI Agent Engine"
    )
    parser.add_argument(
        "--env",
        choices=["dev", "prod"],
        default="prod",
        help="Target environment (default: prod)",
    )
    args = parser.parse_args()
    deploy(args.env)
