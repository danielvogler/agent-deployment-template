# Changelog

All notable changes to this cookiecutter template are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html) — see
[Template Versioning](AGENTS.md#template-versioning) in `AGENTS.md` for what bumps count as
MAJOR/MINOR/PATCH and how releases are tagged.

## [Unreleased]

### Added

- **Dependabot, in both the template and the projects it generates.** Neither had one, so
  nothing tracked uv dependencies, GitHub Actions or pre-commit hook versions. Monthly and
  grouped, with a 7-day cooldown on Python packages; generated projects keep runtime majors
  ungrouped so they arrive one at a time. Security advisories are unaffected by the schedule.

## [2.0.0] - 2026-09-17

### Changed

- **BREAKING: deployed agents now run as `agent-engine-sa`, not the project's shared Reasoning
  Engine Service Agent.** `deploy.py` now always passes a `service_account`, where before it
  passed none, so the next deploy after a `cruft update` fails with `PermissionDenied` on
  `actAs` until the new IAM binding exists.

  **Migration:** re-run `make setup-gcp ENV=<env>` before the next deploy — it adds the binding
  and is safe to re-run. Then check that `agent-engine-sa` holds whatever roles the agent needs
  at runtime, because the identity it runs under genuinely changes. To defer, pin the template
  to the previous release rather than updating.

- **Retracted: "the observability layer has no destination in production."** An earlier draft
  claimed Agent Engine did not forward container stdout, and added a `google-cloud-logging`
  handler to compensate. The diagnosis was wrong: stdout is forwarded, and the missing logs came
  from a disabled `_Default` sink in the GCP project. The handler and its dependency are gone.
  See "Things that will bite you" in `AGENTS.md`.

### Fixed

- `.env.example` was excluded by the generated `.gitignore`'s `.env.*` rule, so the initial
  commit never tracked it and `cp .env.example .env` failed for anyone cloning.
- Generated projects ignored their chosen Python version: `requires-python` set only a floor, so
  `uv sync` took the newest interpreter installed. A `.python-version` file now pins it.
- Local development could not use Application Default Credentials. Nothing set
  `GOOGLE_GENAI_USE_VERTEXAI`, so google-genai used the AI Studio backend and demanded an API
  key even with valid ADC. It now defaults to `TRUE` in `.env.example`.
- `read_traces.py` read `GOOGLE_CLOUD_PROJECT` from the environment but never loaded `.env`,
  then reported "Set GOOGLE_CLOUD_PROJECT in .env" — naming a file it had not read.
- `.cruft.json` could be written with an empty `commit` when generating from a relative path,
  which made a later `cruft check` abort instead of reporting drift.
- `setup_gcp.sh` printed the service-account private key to stdout. It now pipes the value into
  `gh secret set` without rendering it, and documents server-side revocation.
- `make logs` and `make traces` queried the wrong things, and tracing never worked at all.
  `read_logs.sh` filtered on a resource type Agent Engine does not use; `read_traces.sh` printed
  a Cloud Logging filter labelled as a Cloud Trace filter and never called an API. No exporter
  had ever been configured, so `@instrument` produced no spans. Replaced by a unit-tested
  `read_traces.py` against the Cloud Trace v1 API.
- `make setup-monitoring` could not be re-run: the second run failed with "Update Dashboard
  should specify a non empty etag". The script now reads the live etag and injects it.
- Local deploys need `gcloud auth application-default login` as well as `gcloud auth login`,
  and no generated doc said so. The failure arrives after the agent is pickled and uploaded.
- A renamed staging bucket was silently ignored in CI: `setup_gcp.sh` printed
  `GCS_STAGING_BUCKET` as an environment variable while `deploy.yml` read it from `secrets`.
- `cruft create` left every generated project with a dirty working tree, because the post-gen
  hook committed `.cruft.json` before cruft rewrote the same file.
- Generation failed outright on any machine without a configured git identity, and because
  cookiecutter treats a failing post-gen hook as fatal, no project was left behind.
- `hooks/post_gen_project.py` ran `git init` and `git add -A` but never committed, and the
  first fix for that had its own bug.
- `security.yml`'s CodeQL job failed permanently on private repositories without Advanced
  Security. It now probes the API and skips when code scanning is unavailable.
- Generating with `python_version=3.12` produced a project that failed its own `ruff check`.
- Six template source files were not `ruff format` clean, so generated projects failed CI.
- Freshly generated projects failed their own `make pre-commit` before their author had
  written a line.
- Generated `ci.yml` enforced the project-wide coverage gate against each suite separately,
  which neither was meant to clear alone. A `coverage` job now runs them together.
- Generated `eval.yml` pinned Node 20, passed `--ci` (not a recognised flag), and gated on
  promptfoo's exit code, which is `0` even when every case errors. It now parses `output.json`
  and fails on any error or a pass rate below the configured threshold. The eval job likely
  never actually worked in any generated project until this change.
- Generated `README.md` and `CLAUDE.md` documented the wrong default for
  `GOOGLE_CLOUD_LOCATION`.
- Three real make targets were undocumented: `make test-integration`, `make clean` and
  `make help`.

### Added

- Core observability library `agent/observability.py`: structured JSON logging, `@instrument`,
  `log_event` and `redact_pii`, with `severity` and `agent_name` on every event so entries are
  queryable in Cloud Logging rather than plain text.
- Cloud Trace export, enabled per deployment by `CLOUD_TRACE_ENABLED`, off by default so a
  local `make dev` stays offline.
- Cloud Monitoring dashboard and two alert policies under `deployment/monitoring/`, with
  `setup_monitoring.sh` to install them.
- Rollback support: `deploy.yml` accepts an optional `ref`, and `make rollback REF=<tag>`
  redeploys a previous ref against the existing Agent Engine resource.
- Standalone health check at `deployment/scripts/health_check.py`, runnable against an
  already-deployed resource rather than only as part of a deploy.
- cruft integration so generated projects track the template, plus a drift-detection CI job.
- Testing infrastructure: mocked integration tests and skill-segmented promptfoo evals.
- Coverage now measures `deployment/` as well as `agent/`, with new unit tests for the deploy
  path, `check_resource` and `deployment/config.py`.
- `validate-template.yml` generates four cookiecutter variants instead of one, and also runs
  `ruff format --check` and the generated project's own pre-commit set.
- Conventional-commit enforcement on PR titles in generated projects (`lint-pr.yml`), which
  matters because a squash merge uses the PR title as the commit subject.
- Documented dev/prod environment separation, with a required GitHub Environments table.

## [1.1.0] - 2026-07-20

> **Not tagged.** `v1.0.0` and `v1.1.0` were recorded here but never pushed as git tags, so
> `cruft update --checkout v1.1.0` cannot resolve. `v2.0.0` is the first release with a tag;
> pin to that or later. The two sections below are kept as a record of what changed.

First cruft-aware release: generated projects can now track and pull in template updates
via `cruft check`/`cruft update` instead of only being generated once and left to drift.

### Fixed

- `hooks/post_gen_project.py` no longer crashes under `cruft create`/`cruft update`: those
  commands only inject `_template`/`_commit` into the cookiecutter context (not
  `_repo_dir`/`_checkout`, which plain `cookiecutter` provides), and the strict Jinja lookup
  raised `UndefinedError` and aborted generation. All private context lookups now use a
  Jinja `default` so both flows work.

### Added

- Template repo: `cruft` dev dependency for template maintainers to test `cruft create`/`cruft update`
- Generated repo: `.cruft.json` auto-generated by `hooks/post_gen_project.py`, pinning the exact
  template commit used so `cruft check`/`cruft update` can track drift later
- README: documented `cruft create` as the canonical project generation method, with a
  "keeping in sync" section covering `cruft check`/`cruft update`
- Generated repo: `cruft-check.yml` workflow — non-blocking drift check that warns when the
  project has fallen behind the template (`cruft check` on push/PR/weekly schedule)
- Template versioning discipline documented in `CLAUDE.md`, so releases are tagged and
  generated projects have a controlled `cruft update --checkout <tag>` upgrade path

## [1.0.0] - 2026-07-20

Initial template baseline, tagged retroactively as the `1.0.0` reference point that
`1.1.0` and later releases version against. No `v1.0.0` git tag exists — only `v1.1.0`
onward are tagged (see [Template Versioning](CLAUDE.md#template-versioning)).

### Added

- Initial cookiecutter template with full ADK agent scaffold
- `cookiecutter.json` with project metadata and model provider selection
- `hooks/pre_gen_project.py` — input validation before generation
- `hooks/post_gen_project.py` — git init, uv sync, pre-commit install after generation
- Generated repo: Google ADK `root_agent` with `get_current_datetime` and `web_search` tools
- Generated repo: `prompts/` directory with YAML registry for prompt composition
- Generated repo: `deployment/` with Agent Engine deploy script and GCP bootstrap scripts
- Generated repo: `tests/unit/` with tool and model tests
- Generated repo: `tests/evals/` with promptfoo red-team configuration
- Generated repo: GitHub Actions CI, security, eval, and deploy workflows
- Generated repo: `CLAUDE.md` with full developer and AI assistant instructions
- Generated repo: `.claude/commands/` with `/deploy`, `/eval`, `/logs` slash commands
- Template repo: `ci.yml`, `validate-template.yml`, `lint-pr.yml` workflows
- Template repo: `CLAUDE.md` with template contribution instructions
