import re
import sys


def validate_project_slug() -> None:
    slug = "{{ cookiecutter.project_slug }}"
    if not re.match(r"^[a-z][a-z0-9-]+$", slug):
        print(
            f"ERROR: project_slug '{slug}' must be lowercase letters, numbers, and "
            "hyphens only, starting with a letter."
        )
        sys.exit(1)


def validate_email() -> None:
    email = "{{ cookiecutter.author_email }}"
    if not email or "@" not in email:
        print(f"ERROR: author_email '{email}' is not a valid email address.")
        sys.exit(1)


def warn_default_gcp_project() -> None:
    project = "{{ cookiecutter.gcp_project_id }}"
    if project == "my-gcp-project":
        print(
            "WARNING: gcp_project_id is still the default placeholder. "
            "Update GOOGLE_CLOUD_PROJECT in .env before deploying."
        )


validate_project_slug()
validate_email()
warn_default_gcp_project()
