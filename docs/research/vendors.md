---
this_file: docs/research/vendors.md
---

# Vendor repos under `../vendors`

Read-only reference. Researched 2026-10-25 from source; I built nothing.

## pydoccraft (`vendors/pydoccraft`, HEAD `e7e23c44e0109beaaad786d091cada99138f4fbb`, 2026-10-22)

**What it is.** A PyMuPDF-style Python package (`pydoccraft`, import `doc_ex`, version 0.3.0, Apache-2.0) for PDF/DOCX/PPTX extraction, rendering and conversion. One PyO3 extension `doc_ex._core` (built with maturin 1.8.1, `strip = true`; classifiers list Python 3.11-3.13, `requires-python >=3.11`) over thin Rust adapters (`pdf.rs`, `docx.rs`, `pptx.rs`, `convert.rs`). Native boundary is three calls: `extract(data, filetype, password)` returns JSON, `convert(data, src, dst, password)` returns bytes, `render(data, filetype, page, dpi)` returns PNG bytes. Python owns the object model; upstream Rust types are never exposed.

**Cargo dependency approach** (`Cargo.toml`):
- Git dependencies pinned to full SHAs, one SHA per upstream repo. All pins point at the author's reviewed forks (`github.com/narain1/{deckcraft,pdfcraft,wordcraft}`), not at `storytold`. Upstream bases are recorded in AGENTS.md.
- Crates linked: `deckcraft-model/pdf/pptx/render` (rev `16de1ca8...`); `pdfcraft-annot/content/cos/create/edit/export/fonts/forms/model/organize/render` (rev `516caea9...`); `wordcraft-doc/docx/layout/pdf/render` (rev `a57b4167...`). `craft-libs` (rev `c3487320...`) is reached transitively for `krilla`/`craft-pdf`. Also pins `pyo3 =0.23.5`, `kurbo`, `skrifa`, `quick-xml`, `png`, `zip` (deflate only) with exact `=` versions.
- Deliberately **not** linked: any `*-engine`, `ui-egui`, `mcp`, `automation`, `ocr`, `sign`, `js`, `print`, `platform`, or media codec crates.
- Root `[patch.crates-io]` re-declares `hayro`, `hayro-interpret`, `hayro-jbig2`, `hayro-syntax`, `lopdf` from a local `vendor/pdfcraft/` copy (4 MB) and `krilla` from craft-libs, because dependency-workspace patches do not propagate. Anyone linking PdfCraft crates must do the same.
- `Cargo.lock` committed; exact versions; permissive-only license graph with generated `THIRD_PARTY_LICENSES.md`; wheels carry `LICENSE-THIRD-PARTY`.

**Wheel size** (from `.kiro/specs/rust-document-engine/validation.md` and `docs/development.md`, Linux x86_64 manylinux, CPython 3.11): 13.2 MB (13,198,994 bytes) to 17.4 MB across versions; one run 16.4 MB with a 38 MB uncompressed extension, another 14.4 MB with 33 MB. Uncompressed extension 28.6-40.3 MB. No other platforms measured by me. So a wheel linking only PDF + DOCX + PPTX engines costs roughly 13-17 MB; full editors (engine crates) would be far larger [estimate, not measured].

**Lessons for mcruft.**
1. Link format/model/render crates only; pydoccraft's AGENTS.md lists exactly what to avoid (same list as mcruft's AGENTS.md).
2. Pin by SHA, one SHA per repo, upgrade as a dedicated change with wheel-size and corpus rerun. Copy upstream `[patch]` blocks into the root manifest.
3. Fork-pinning is a real risk: pydoccraft's upstream fixes (integer rasteriser, fallible rendering) live in forks that may diverge from `storytold`. mcruft should pin `storytold` revisions unless a fix is only in a fork.
4. Keep the Rust boundary to bytes in / JSON or bytes out; do not expose Rust types.
5. Documents are untrusted: bound input size, page count, image size, archive expansion; map errors to stable Python exceptions; no panics, no runtime downloads, no subprocess.
6. It covers only PdfCraft, WordCraft, DeckCraft and is read/extract/convert oriented. It has no VectorCraft, PhotoCraft or DesignCraft, and no editing. Document-model editing is out of its scope.
7. Needs Rust 1.95; the author builds in Docker because the host may lack Rust.

## craft-suite-api (`vendors/craft-suite-api`, HEAD `82ea10ef2f21a881ae7931985983163cf4d412ee`, 2026-10-23)

Python package `craft_suite_api` with an MCP command `craft-suite-mcp`, built on a connector SDK (its AGENTS.md defers to Knuckles-Team org rules; I did not inspect the SDK). It wraps **the ArtCraft Services backend** (an HTTPS service), exposing 9 read operations (status alert, model catalogs for audio/image/mesh/splat, tags, folders) through a few MCP tools. The README itself says it is "not a connector to Craft documents or the native ArtCraft desktop editor" and that 259 documented backend operations remain unimplemented. Writes are off by default (`CRAFT_SUITE_API_ALLOW_WRITES`). **Not evidence of desktop-product capability; ignore for mcruft's engines.** Possibly useful later only as a pattern for confirmation-gated effects.

## artcraft-in-a-box (`vendors/artcraft-in-a-box`, HEAD `a7ed363b56402c35ecd5677d2ca233e2ba2638fc`, 2026-10-24)

An nginx container that self-hosts the **WebAssembly builds** of the apps (no server code; files stay in the browser). `apps.json` is the single source of truth: per app GitHub repo, release tag, `<id>-web-<version>.zip` asset and SHA-256. Currently serves PhotoCraft v0.15.1, VectorCraft v0.16.0, FilmCraft v0.12.0, LightCraft v0.13.0, PrintCraft v0.2.1 (built from `storytold/pdfcraft`), EffectCraft v0.16.0, DesignCraft v0.12.0. **DeckCraft is not in the list.** 279 MB of wasm becomes 107 MB gzipped; image about 170 MB.

**Lessons.** (1) Every app has an official release asset naming scheme and tags that match the installed CLI versions for VectorCraft, PhotoCraft and DesignCraft (the PdfCraft asset is PrintCraft 0.2.1, a different number from CLI 0.13.0), a good source of "pin to a release tag" revisions. (2) PdfCraft's repo ships a web app under the name PrintCraft, so product naming is unstable across assets. (3) WASM builds are an alternative distribution/execution path but are GUI apps, not importable libraries, and need HTTPS for WebGPU/clipboard; they do not help the Python wheel goal.
