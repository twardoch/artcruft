---
this_file: WORK.md
---

# Task 5 scaffold

Implemented the six-package uv workspace, public model/API, safe folder package I/O,
entry-point router, CLI lookup/runner, lib inspection and PDF extraction/combination,
optional async MCP session, five product declarations, optional native proof binding,
and CLI wheel builder. Conversion adapters remain Task 6 stubs. No commits made.

Interpretations and limits:

- Unsaved `add_file` retains an external reference until the first save (§6).
  On saved documents it copies immediately (§3); subsequent saves preserve asset bytes.
- Asset paths are absolute in memory and relative POSIX paths in manifests.
- SVG viewBox coordinates and unitless dimensions use CSS pixels (96/in), converted
  to points (72/in). Explicit pt/mm/in dimensions are supported when no viewBox exists.
- Non-conversion reports use policy `None`; hash mismatches on load emit UserWarning.
- Composite fidelity capabilities retain the matrix's verification labels and notes
  explaining required outline/render passes. DesignCraft file-input routes are unverified.
- MCP uses async open/call/close and an async context manager in the same task.
- Binary extras retain their distribution dependencies. Because uv resolves even
  unselected extras and these five distributions are unpublished, workspace-only
  `exclude-dependencies` omits them. Remove those exclusions when wheels are available;
  until then, install locally built wheels separately. Workspace bundled extras do
  not install binaries while these exclusions remain.

Verification (2026-10-25):

- No pre-existing Python scaffold or test suite was present.
- `uv sync --all-packages`: all six workspace distributions installed successfully.
- `uv run ruff check .`: all checks passed.
- `uv run ruff format --check .`: all files already formatted.
- `uv run pytest -q`: 36 passed, 1 skipped with the base dependencies.
- Supplemental `uv sync --all-packages --extra mcp` and `uv run pytest -q`:
  36 passed, including the official SDK against a local stdio fixture. No product
  CLIs or network calls are used by tests.
- One `cargo check --manifest-path native/mcruft_pdfcraft_native/Cargo.toml`:
  passed, `Finished dev profile [unoptimized + debuginfo] ... in 46.59s`.
  Cargo warned that hayro, hayro-interpret and lopdf patches are unused by this
  minimal graph; all five requested patches remain pinned to the same revision.
- Protected SPEC.md, PLAN.md, AGENTS.md and all existing docs/ files verified by SHA-256.

Not checked: native runtime/wheel build, actual product conversions, real fat-binary
thinning or redistribution of product binaries/licenses. Native Cargo.lock and uv.lock
are included for reproducibility. Task 6 remains outside this change.

Official references consulted: [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/),
[uv exclusions](https://docs.astral.sh/uv/reference/settings/#exclude-dependencies),
[hatch-vcs](https://github.com/ofek/hatch-vcs), [MCP SDK](https://py.sdk.modelcontextprotocol.io/),
[pypdf](https://pypdf.readthedocs.io/en/stable/user/merging-pdfs.html),
[python-pptx](https://python-pptx.readthedocs.io/en/latest/api/presentation.html),
[Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html),
[PyO3](https://pyo3.rs/main/module.html), and the pinned PdfCraft source.
