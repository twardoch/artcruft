---
this_file: WORK.md
---

# Work status

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
- **Bundled CLI wheel:** `tools/bundle_cli.py vectorcraft` writes a 51 MB arm64 wheel. It
  installs, runs, and is found without `PATH`.
- **Native binding:** `maturin build` produces an abi3 wheel. Once it is installed, the router
  sends PDF page extraction and combination to `pdfcraft-native`.

## Next

- Task 7 (publish): push `mvp` and open a PR. Merging to main and uploading to PyPI need an owner
  decision.
- Deferred minors: see the review notes summarised in the project CHANGELOG. They include:
  - Losses are not attributed to pages.
  - Some raw library errors are not wrapped in `McruftError`.
  - `engines()` checks CLIs one after another.
  - The outline pass fails on an empty document.
- Batch 2 products and the time-based media operations (SPEC §8).
