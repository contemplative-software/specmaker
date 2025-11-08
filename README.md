<div align="center">

  <img src="SpecMakerLogoFilled.svg" alt="SpecMaker Logo" width="300"/>

  <h3>Multi‑agent documentation review for spec‑driven development</h3>

</div>

<div align="center">

  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license"></a>
  <img src="https://img.shields.io/badge/python-3.13%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/status-alpha-orange" alt="status">
  <a href="https://github.com/contemplative-software/specmaker/actions/workflows/ci.yml"><img src="https://github.com/contemplative-software/specmaker/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/contemplative-software/specmaker"><img src="https://codecov.io/gh/contemplative-software/specmaker/branch/main/graph/badge.svg" alt="Coverage"></a>

</div>

---

**Website**: [https://specmaker.dev](https://specmaker.dev)
**CLI**: Coming Soon!

---

# SpecMaker

SpecMaker is a multi‑agent documentation system that guides engineers through structured, human‑in‑the‑loop flows to produce high‑quality, consistent, and AI‑readable specs. It is a companion at the beginning of spec‑driven development — Requirements → Design → Tasks — helping you gain confidence in your problem definitions (requirements), sharpen design decisions, and produce a concrete implementation plan (tasks). Before handing your spec to a coding agent, SpecMaker helps you develop a strong mental model of what you’re building and align that intent with AI.

This repository contains the Python core library powering SpecMaker. It builds on modern Python tooling, type‑safety, and validation with Pydantic v2, as well as agent orchestration with PydanticAI and DBOS.

## Status

Alpha (v0.0.1). Interfaces and APIs may change.

## Features

- Multi‑agent authoring flow (Architect → Writer → Reviewer)
- Human‑in‑the‑loop checkpoints and approvals
- Durable orchestration via DBOS + PydanticAI (pause/resume, retries)
- SQLite‑backed persistence and metadata extraction

## How it works

Currently, SpecMaker ships the `/review` workflow. Provide an existing manuscript; the Reviewer agent evaluates it, may request clarifications from you or loop with the Writer for edits; on approval, results are persisted.

```mermaid
flowchart TD
  A["User provides prompt/doc"] --> B["/review workflow"]
  B --> C["Reviewer (agent)"]
  C -->|needs clarification| A2["Collect clarifications"] --> C
  C -->|edits requested| D["Writer (agent)"] --> C
  C -->|approved| E["Persist result"]
```

**`/init` command** — Initialize SpecMaker for a project by collecting user and project details, then creating the `.specmaker/` folder with initial configuration and metadata files.

### Coming soon

**`/write-and-review` workflow** — Full authoring flow from outline to final manuscript. The Documentation Architect drafts an outline (with your approval), the Technical Writer produces the manuscript, and the Reviewer evaluates and may loop for edits or clarifications.

```mermaid
flowchart TD
  UI["User Input"] --> WF["DBOS Workflow: /write-and-review"]
  WF --> ARCH["Documentation Architect (Agent)"]
  ARCH -->|outline approved - Deferred Tool| WRITER["Technical Writer (Agent)"]
  WRITER --> REVIEWER["Reviewer (Agent)"]
  REVIEWER -->|needs user clarification - Deferred Tool| UI_CLAR["Collect clarifications"] --> WRITER
  REVIEWER -->|edits requested| WRITER
  REVIEWER -->|approved| PERSIST["Persist + Metadata Extraction (Step)"]
```

## Getting Started (from source)

This project uses the `uv` Python toolchain for dependency management and execution.

```bash
# Clone your fork and enter the repo
git clone <your-fork-url>
cd specmaker

# Set up the Python environment
uv sync

# Run tests
uv run --frozen pytest -q

# Lint, format, type-check
uv run --frozen ruff format .
uv run --frozen ruff check .
uv run --frozen pyright
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

Inspired by excellent open‑source practices from [Pydantic](https://github.com/pydantic/pydantic) and others.



