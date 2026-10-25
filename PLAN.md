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
uv workspace per SPEC: `packages/mcruft` (core model, `.mcruft` read/write, engine
registry, CLI + MCP engine adapters), `packages/mcruft_<app>` x5 (engine declarations),
one maturin native-binding skeleton, the bundled-wheel mechanism (script that vendors
the `<app>-cli` binary into a platform wheel). Tests run with `uvx hatch test` or
`uv run pytest`.

### Task 6: MVP operations
Implement end-to-end: open/inspect (pdf, pptx, svg, png), page split/merge, export to
pdf/png/svg, pdf → pages in a `.mcruft` package, editable vs fidelity conversion for at
least pptx→pdf and pdf→svg, with tests against the real CLIs (skipped when missing).

### Task 7: Publish
Quality gate (slop clean, verification, code review), README/CHANGELOG, push to GitHub.
