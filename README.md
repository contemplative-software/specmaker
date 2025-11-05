# SpecMaker

SpecMaker is a multi‑agent documentation system that guides engineers through structured, human‑in‑the‑loop flows to produce high‑quality, consistent, and AI‑readable specs.

This repository contains the Python core library powering SpecMaker. It builds on modern Python tooling, type‑safety, and validation with Pydantic v2.

## Status

Alpha (v0.0.1). Interfaces and APIs may change.

## Features

- Structured, stepwise authoring flows
- Strong typing and validation with Pydantic v2
- Settings management via pydantic‑settings
- Extensible agent pipeline architecture

## Getting Started (from source)

This project uses the `uv` Python toolchain for dependency management and execution.

```bash
# Clone your fork and enter the repo
git clone <your-fork-url>
cd specmaker

# Set up the Python environment
uv sync

# Run tests
uv run pytest -q

# Lint, format, type-check
uv run ruff format .
uv run ruff check .
uv run pyright
```

See `specmaker-core/README.md` for additional development notes and Docker/Devcontainer usage.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on setting up your environment, coding standards, and how to submit pull requests.

## Security

If you believe you’ve found a security vulnerability, please follow the process in [.github/SECURITY.md](.github/SECURITY.md).

## License

This project is licensed under the MIT License – see [LICENSE](LICENSE) for details.

## Citation

If you use SpecMaker in academic work, please see [CITATION.cff](CITATION.cff).

## Acknowledgements

Inspired by excellent open‑source practices from Pydantic and others. Pydantic repository: `https://github.com/pydantic/pydantic/tree/main`.


