# Changelog

All notable changes to this cookiecutter template are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

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
