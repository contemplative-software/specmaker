# Contributing to SpecMaker

Thanks for your interest in contributing! This document describes how to set up your environment, run checks, and submit high‑quality pull requests.

SpecMaker follows modern Python practices and uses the `uv` toolchain for dependency management and execution. Please avoid `pip` directly.

## Prerequisites

- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) installed
- Git and a GitHub account
- Optional: Docker (for containerized workflows)

## Setup

```bash
# Fork the repo on GitHub, then clone your fork
git clone <your-fork-url>
cd specmaker

# Create the virtual environment and install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

## Development workflow

Run the following before submitting a pull request:

```bash
# Format and lint
uv run --frozen ruff format .
uv run --frozen ruff check .

# Type-check
uv run --frozen pyright

# Tests (quick)
uv run --frozen pytest -q

# Tests with coverage
uv run --frozen pytest --cov=src/specmaker_core --cov-report=term-missing
```

Guidelines:

- Follow type hints everywhere (Pyright strict mode is enabled).
- Keep functions small and well‑named; prefer readability over cleverness.
- Add tests for new features and bug fixes; include regression tests where applicable.
- Update docs and examples if behavior changes.
- Use Conventional Commits for commit messages (e.g., `feat:`, `fix:`, `docs:`, `refactor:`).

## Pull requests

1. Create a feature branch from `main` (e.g., `feat/awesome-thing`).
2. Make focused changes; keep PRs small and easy to review.
3. Ensure the checklist in the PR template is satisfied.
4. Link related issues.
5. Be responsive to review feedback.

## Reporting issues

Please use the issue templates to report bugs and request features. Include:

- What you did
- What you expected to happen
- What actually happened
- Environment details (Python version, OS)
- Minimal reproducible example, if possible

## Security

If you discover a security vulnerability, please follow the steps in [.github/SECURITY.md](.github/SECURITY.md).

## License

By contributing, you agree that your contributions will be licensed under the MIT License.


