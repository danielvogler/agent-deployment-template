import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _project_name() -> str:
    """Read the project name from pyproject.toml so derived names stay in sync."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject, "rb") as f:
        return tomllib.load(f)["project"]["name"]


def resolve_model():
    """Return the ADK-compatible model handle based on MODEL_PROVIDER env var.

    Supported values for MODEL_PROVIDER:
      google    (default) — Gemini 2.5 Pro via native ADK
      anthropic           — Claude via LiteLLM
      openai              — GPT-4o via LiteLLM
      litellm             — any model; set LITELLM_MODEL to the full model string
    """
    provider = os.getenv("MODEL_PROVIDER", "google").lower()

    if provider == "google":
        return "gemini-2.5-pro"

    from google.adk.models.lite_llm import LiteLlm  # noqa: PLC0415

    match provider:
        case "anthropic":
            return LiteLlm(model="anthropic/claude-opus-4-8")
        case "openai":
            return LiteLlm(model="openai/gpt-4o")
        case "litellm":
            model = os.environ["LITELLM_MODEL"]
            return LiteLlm(model=model)
        case _:
            raise ValueError(
                f"Unknown MODEL_PROVIDER: {provider!r}. "
                "Valid options: google, anthropic, openai, litellm"
            )


# The service account `setup_gcp.sh` creates, and the staging bucket it provisions.
# Both are fully determined by the project id, so neither has to be restated in .env
# -- keep these in step with SA_NAME and BUCKET in deployment/scripts/setup_gcp.sh.
RUNTIME_SA_NAME = "agent-engine-sa"
STAGING_BUCKET_SUFFIX = "-agent-staging"


def default_service_account(project: str) -> str:
    """The runtime identity `setup_gcp.sh` provisions for this project."""
    return f"{RUNTIME_SA_NAME}@{project}.iam.gserviceaccount.com"


def default_staging_bucket(project: str) -> str:
    """The staging bucket `setup_gcp.sh` provisions for this project."""
    return f"gs://{project}{STAGING_BUCKET_SUFFIX}"


def normalise_bucket(value: str) -> str:
    """Add the `gs://` scheme if the caller left it off.

    `setup_gcp.sh` prints the bucket as a bare name while the docs show it with the
    scheme, and Vertex wants a full `gs://` URI -- so accept either spelling rather
    than making the difference matter.
    """
    return value if value.startswith("gs://") else f"gs://{value}"


@dataclass
class DeploymentConfig:
    project: str
    location: str
    staging_bucket: str
    resource_name: str | None
    agent_display_name: str
    gcs_dir_name: str
    service_account: str

    @classmethod
    def from_env(cls) -> "DeploymentConfig":
        """Build the config from the environment.

        `GOOGLE_CLOUD_PROJECT` is the only required variable. The staging bucket and
        the runtime service account are derived from it, matching what
        `setup_gcp.sh` provisions, and the corresponding environment variables exist
        only to override that for a renamed bucket or SA.
        """
        project = os.environ["GOOGLE_CLOUD_PROJECT"]
        staging_bucket = os.getenv("GCS_STAGING_BUCKET")
        service_account = os.getenv("AGENT_ENGINE_SERVICE_ACCOUNT")
        return cls(
            project=project,
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1"),
            staging_bucket=(
                normalise_bucket(staging_bucket)
                if staging_bucket
                else default_staging_bucket(project)
            ),
            resource_name=os.getenv("AGENT_ENGINE_RESOURCE_NAME") or None,
            agent_display_name="{{cookiecutter.project_name}}",
            # Staging subfolder, project-named so several agents can share one
            # bucket instead of colliding in the SDK's generic default.
            gcs_dir_name=_project_name(),
            # Always set: omitting it silently falls back to the project's shared
            # Reasoning Engine Service Agent. See "Runtime identity" in AGENTS.md.
            service_account=service_account or default_service_account(project),
        )

    @property
    def runtime_env_vars(self) -> dict[str, str]:
        """Environment variables set on the deployed container.

        Deliberately minimal. Logs need nothing here; traces need both of these,
        and neither is optional. See "Observability -> Destinations" in AGENTS.md.
        """
        return {
            "CLOUD_TRACE_ENABLED": "true",
            "OTEL_EXPORTER_GCP_TRACE_PROJECT_ID": self.project,
        }
