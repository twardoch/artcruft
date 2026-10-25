---
this_file: PLAN.md
---

# mcruft MVP plan

Source brief: `../issues/101.md`. Agent rules: `AGENTS.md`.

One sentence: a unified Python API for paged 2D documents (and embedded media) that
routes operations to ArtCraft engines (Rust bindings, CLIs, MCP servers) and native
Python/Rust format libraries, stored in a `.mcruft` package folder.

## Global Constraints

- Packages: metapackage `mcruft`; per-product `mcruft_vectorcraft`, `mcruft_deckcraft`,
  `mcruft_photocraft`, `mcruft_pdfcraft`, `mcruft_designcraft`. Python >= 3.12, uv
  workspace, hatch-vcs versioning.
- The top-level API models Document → Page → Frame (text, vector, image, media) plus
  embedded media. Products are engines picked by capability, never the API structure.
- Every conversion offers two policies: `editable` (keep structure, may lose fidelity)
  and `fidelity` (keep appearance, may lose editability). Losses are reported, not hidden.
- `.mcruft` is a folder package: a manifest (JSON) + native asset files (ArtCraft native
  or reference formats such as .pdf/.pptx/.svg/.psd/.idml) + optional single-page PDF
  previews. Assets are referenced, not re-encoded into an internal format.
- Engines: CLI (`<app>-cli run`/`commands`), MCP (`<app>-cli mcp`, stdio), native
  bindings (PyO3/maturin over engine crates pinned to commit SHAs; never UI/MCP/CLI/
  updater/network crates). CLI flags differ per app; verify per app.
- Bundled wheels: each product's wheel is a separate package; no runtime downloads.
- Vendors under `../vendors/` are reference only; never path-import them.
- Don't over-engineer, over-test, over-document. Batch-2 products are out of scope.

## Tasks

### Task 1: Product research
Write `docs/research/products/<app>.md` for vectorcraft, deckcraft, photocraft, pdfcraft,
designcraft, plus `docs/research/products/README.md` (comparison matrix). For each:
read/write formats; CLI subcommands and flags (from `<app>-cli --help` and
`<app>-cli commands`); MCP tools (from source / `tools/list`); Rust crates that are
bindable (engine/format/model/render/pdf) vs not (ui, mcp, automation); key command ids
for open/save/export/page ops; native file format; gaps vs the reference product.
Also summarise lessons from `../vendors/pydoccraft`, `../vendors/craft-suite-api`,
`../vendors/artcraft-in-a-box` in `docs/research/vendors.md`.

### Task 2: Native-format library research
Write `docs/research/native-libs.md`: candidates for pdf, svg, psd, pptx, docx, xlsx
(Rust with Python bindings preferred, then pure Python). Per lib: license, maintenance
(last release, stars), Python wheels, bundled native deps, read/write capabilities. End
with a selection table for the MVP and rationale.

### Task 3: Spec
Write `SPEC.md`: object model (Document, Page, Frame kinds, Media, Asset), `.mcruft`
package layout + manifest JSON schema, engine/capability registry and routing, conversion
matrix with editable vs fidelity policies, operations list (split/merge pages, export
pdf embedded-fonts/outlined-fonts/png/svg, import pdf/images as pages, frame round-trip to
a specialist engine, video keyframes ↔ slides), package layout of the repo and wheels.
Based on Tasks 1–2.

### Task 4: Agent framework
Update `AGENTS.md` and write `docs/workflow.md`: how work is delegated (codex relay,
claude subagents, max two concurrent), review gates, test commands, release steps.

### Task 5: Scaffold
Per SPEC.md §3, §4, §6 and §9, set up a uv workspace with these parts:
- `packages/mcruft`:
  - the model
  - `.mcruft` package I/O following the §3 rules
  - Report, Loss and the errors
  - a router with entry-point discovery
  - a CLI runner
  - a lib engine covering the §4 inspect table
  - an MCP session under the `[mcp]` extra
- `packages/mcruft_<product>` ×5: engine declarations (binary lookup, version, the capabilities from §5). Adapters may be stubs that raise `UnsupportedRoute` until Task 6.
- `native/mcruft_pdfcraft_native`: a maturin skeleton, kept outside the workspace.
- `tools/bundle_cli.py`: builds the arm64 `mcruft-<product>-bin` wheel.

Gates: `uv run ruff check .` and `uv run pytest -q`.

### Task 6: MVP operations
Implement the SPEC §5 routes and the §5.2 export pipeline end to end:
- open/inspect for pdf, pptx, svg and png
- `add_file`
- manifest-level split/merge
- save/load with previews
- export to pdf, png, svg and pptx under both policies
- convert pptx→pdf and pdf→svg under both policies
- the outline pass
- page-level `edit_in`

Tests run against the real CLIs, are skipped when a binary is missing, and write only under `tmp_path`.

### Task 7: Publish
Quality gate (slop clean, verification, code review), README/CHANGELOG, push to GitHub.
