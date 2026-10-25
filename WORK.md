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
- SVG absolute width/height take priority, supporting px/pt/mm/cm/in; unitless values
  use CSS pixels (96/in), converted to points (72/in). Missing or percentage dimensions
  fall back to viewBox coordinates, also treated as CSS pixels.
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

## Scaffold fix round 1

- I1: prefer absolute SVG dimensions over viewBox, including centimetres. Added one
  parametrized regression test for A4, cm, unitless dimensions and viewBox fallbacks.
- I2: engine listing catches McruftError from availability/version checks and marks
  that engine unavailable without stopping discovery. Added one regression test with
  an environment-selected shell script that exits 1 on the version command.
- Gates: Ruff check and format check passed; pytest: 43 passed, 1 optional MCP test skipped.
- No commits; no conversion adapters or native code changed.

## Task 6b: core orchestration

- Added capability-routed direct/composite conversion and PDF/PNG/SVG/PPTX document
  export in `ops.py`; model methods delegate to it. Every engine selection uses the
  registry, including PDF extraction/combination and outline/deck passes.
- Added exact-path page rendering and page edit transactions with derived-asset
  provenance, unchanged-file cleanup and rollback on exceptions. Page ownership is
  kept in memory and rebound after load, split and merge; manifests stay unchanged.
- Added embedded-font PDF previews, regeneration for missing/stale previews and
  removal of unused preview asset references. Preview relocation stages all pages
  before replacing paths, preserving reordered pages. Save stages model changes
  until the manifest replacement succeeds.
- Fixed unavailable/unknown engine pins to raise EngineUnavailable.
- Product-package exception: VectorCraft lacked `export_pages svg -> png (fidelity)`.
  The real `test_export_svg_png_page_contract` failed with
  `vectorcraft: export_pages .svg -> .png (fidelity)` before the fix. Added paged PNG
  export using its existing convert/artboard/scale flags, with standard numbered
  filenames; the declared-capability test exercises all three supported input types.
- Baseline: 50 passed, 1 skipped in 19.78s. Pure orchestration tests: 21 passed.
  Real acceptance checks verify mixed PPTX/SVG page counts, embedded versus outlined
  fonts, both conversion helpers, PNG dimensions at 72 dpi, three image slides and
  reopened preview PDF page counts/hashes. No remaining real-CLI route failures.
- No new dependencies. No commits. SPEC.md, PLAN.md, AGENTS.md, docs/ and vendors
  were not edited. Optional MCP and interactive GUI editing are outside these checks.
- Sandbox invocation uses `UV_CACHE_DIR=/tmp/mcruft-uv-cache` because the default uv
  cache is not writable here.
- Final gates: `uv sync --all-packages` resolved 48 packages and checked 18;
  Ruff check passed, format check found 51 files already formatted;
  `uv run pytest -q`: **75 passed, 1 skipped in 19.85s** (optional MCP SDK absent).

## Task 6 fix round 1

- Re-read amended SPEC §5/§5.2/§7 and both Task 6 reviews. No spec, plan, agent-file
  or vendor edits. No commits.
- Before fixes: 39 focused regression cases failed, covering S1, asset protection,
  atomic PDF output, render siblings, native edit copies/indexes, edited size,
  in-place conversion, missing parents, image validation, JPEG and metadata.
  Two further tests first failed for direct editable raster-to-PDF conversion and
  single-page PdfCraft handoff from a multi-slide asset, then passed after fixes.
- Split page pipelines into `page_ops.py` and split orchestration tests. Touched
  Python modules remain below 200 lines. Fallbacks use declared capabilities;
  raster pages use fidelity conversion under either policy without synthetic losses.
  Pillow supplies DPI-aware raster page rendering through the lib engine.
- Native edit handoffs copy whole assets and retain page indexes. Other handoffs
  use one editable conversion; PDF results are extracted to the selected page.
  Inspection updates page size only after successful edits.
- Added a four-page real-CLI PPTX/SVG/PNG export/preview/PNG test. DeckCraft's PNG
  selection was already correct: the new hash/order test passed before changes.
  Forcing every render to slide 0 caused that test to fail as intended.
- Added direct pypdf dependencies to VectorCraft/PdfCraft, license metadata to all
  six packages, and shared JPEG/TIFF alias normalization (no TIFF routes invented).
- A gate found three formatting-only comment-spacing differences in the current
  README Python example; applied Ruff formatting to that file alone.
- Baseline: 75 passed, 1 skipped in 22.39s. Core suite after fixes: 101 passed,
  1 skipped in 24.72s. Optional MCP remains skipped; GUI editing is not exercised.
- Final gates: sync resolved 48 packages/checked 18; Ruff check passed; format
  check found 59 files already formatted; pytest: **115 passed, 1 skipped in 26.52s**.
  Installed distribution metadata also confirms all six Apache-2.0 license
  expressions and both direct pypdf requirements. No remaining requested failures.

## Task 6 fix round 2

- Re-read amended SPEC §1.2 and §5. No commits or spec/vendor changes.
- R2-1: changed working files survive inspection and caller-body failures. Completed
  edits are registered before inspection; inspection errors propagate with the old
  page size, as documented in the context manager docstring. Failed bodies retain
  changed files without modifying the document. Three inspection-error cases and
  one body-error case failed before this change, then passed.
- R2-2: added explicit fidelity-request/editable-only fallback and fidelity-priority
  cases, both asserting the subsequent outline pass. Existing code passed; in-memory
  mutations removing fallback or reversing priority were both detected by the tests.
- R2-3: editable PNG export raises the specified UnsupportedRoute before output;
  Page.render still uses fidelity. R2-4: PNG/JPG rendering explicitly drops ICC
  metadata and records the specified effects loss only when a profile exists.
  These policy/profile regressions failed before the fixes and now pass.
- R2-5: removed unused Fake capabilities from native target-format tests and added
  a byte-for-byte native-copy assertion. Focused checks: 25 passed in 0.44s.
- Final gates: Ruff check passed; 60 files already formatted; pytest:
  **126 passed, 1 skipped in 27.81s**. The skipped test requires the optional MCP SDK.
