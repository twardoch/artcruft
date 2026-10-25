---
this_file: WORK.md
---

# Work status

## Optional native-format libraries (2026-10-25)

- Added core-only `pdf`, `svg`, `psd` and combined `libs` extras; `engines` still
  installs only product packages. Updated uv.lock and the spec, README and dependency list.
- LibEngine delegates optional PDF rendering, SVG rendering and PSD inspection to
  three small modules. Capabilities use `find_spec` and include package versions;
  verified library routes win over CLI routes without router changes.
- PDFium import, document/page/bitmap operations and cleanup share a module lock.
  SVG uses zoom = dpi/96 with the parser fixed at 96 dpi, avoiding double scaling
  physical units. PSD resolution is 16.16 fixed-point; missing metadata means 72 dpi.
- Baseline: 139 tests passed. Before implementation, the new tests had 9 expected
  failures (missing routes and CLI selection). Focused tests now pass all 25 cases:
  page ordering/names, multiple DPIs, PSD resolution/fallback, verified routing,
  absent modules, invalid page selections/DPI and PDFium lock coverage.
- Public API checks passed: multi-page PDF conversion to numbered PNGs, SVG
  `Page.render` at 96 dpi, and opening a PSD all use the library engine.
- Final gates: `uv lock` and `uv sync --all-packages --all-extras` succeeded;
  `uv run ruff check .` passed; `uv run ruff format --check .` reported 68 files
  already formatted; `uv run pytest -q` finished with **164 passed in 30.18s**.
  Used `UV_CACHE_DIR=/tmp/mcruft-uv-cache` because the default cache is outside the sandbox.
  No product packages or vendor files edited; no commit made.

## Done (MVP, branch `mvp`)

PLAN.md Tasks 1–6 are complete. Each code task passed an independent review, and the branch
passed a whole-branch review followed by one fix wave.

- **Gates:** `uv run ruff check .` and `uv run ruff format --check .` are clean. `uv run pytest -q`
  gives 138 passed and 1 skipped (the optional MCP SDK test), run against the installed ArtCraft
  CLIs: vectorcraft 0.16.0, deckcraft 0.10.0, photocraft 0.15.1, pdfcraft 0.13.0 and
  designcraft 0.12.0.
- **End-to-end checks:**
  - A document built from pptx, svg and png pages saves with previews and reloads.
  - It exports to PDF under both policies (fonts are embedded in editable and outlined in
    fidelity), and to PNG and PPTX.
  - Split, merge and both convert variants work.
- **Bundled CLI wheels:** all five products build arm64 wheels of 29–51 MB, each with a NOTICE.
  They install and run `--version`. The VectorCraft one was also found without `PATH`.
- **Metapackage:** `mcruft[engines]`, built from wheels into a clean venv, registers all seven
  engines.
- **Native binding:** `maturin build` produces an abi3 wheel. Once it is installed, the router
  sends PDF page extraction and combination to `pdfcraft-native`.

## Next

- Task 7 (publish): `mvp` is pushed as PR #1. The slop-clean pass was skipped. Merging to main and uploading to PyPI need an owner
  decision.
- Deferred minors: see the review notes summarised in the project CHANGELOG. They include:
  - Losses are not attributed to pages.
  - Some raw library errors are not wrapped in `McruftError`.
  - `engines()` checks CLIs one after another.
  - The outline pass fails on an empty document.
- Batch 2 products and the time-based media operations (SPEC §8).
