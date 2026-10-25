---
this_file: SPEC.md
---

# mcruft specification (MVP, v0.1)

mcruft is a Python API for paged 2D documents. It treats documents as ordered pages that point
into native files, and it routes each operation to whichever engine can do it: an ArtCraft CLI, an
ArtCraft MCP server, a native binding to ArtCraft Rust crates, or a third-party format library.
The engines are means, not the model.

Evidence: `docs/research/products/`, `docs/research/native-libs.md`,
`docs/research/conversion-probe.md`, `docs/research/wheels-and-probe-2.md`. A route marked ✓ was
run on the cited input; ~ is documented but not run; ✗ is unsupported, with a reason.

## 1. Principles

1. **Index, don't ingest.** A document is a list of pages, each a reference to a page inside a
   native asset (`deck.pptx#2`, `art.vectorcraft#0`, `scan.pdf#5`). Assets are stored as they are
   and are never translated into an internal format.
2. **Two policies, always.** Every conversion and every export takes `policy="editable"` (keep
   structure; may lose appearance) or `policy="fidelity"` (keep appearance; may lose structure).
   There is no default: the caller must choose. When a policy is impossible for a route, mcruft
   raises `UnsupportedRoute` with the reason. Neither policy is ever silently substituted for the
   other.
3. **Losses are data.** Every operation returns a `Report` with losses and warnings. Engine
   warnings are passed through verbatim.
4. **One coordinate convention.** Points (1/72 in), origin top-left, y down; pages are 0-based in
   the API. Adapters convert: PdfCraft and DesignCraft exports are 1-based; DesignCraft rects are
   `[x0,y0,x1,y1]` and DeckCraft rects `[x,y,w,h]`; pixel images use their DPI metadata, else
   72 dpi (1 px = 1 pt).
5. **Small core.** The `mcruft` core is pure Python, with dependencies limited to `pypdf`,
   `python-pptx` and `Pillow`. Product engines are separate packages.

## 2. Object model

```text
Document
  meta: title, created, modified
  assets: {asset_id: Asset}
  pages: [Page]
  media: [Media]                # stored and referenced only in the MVP (§8)

Asset                           # one file inside the package (or an external path before saving)
  id, path, media_type, sha256
  role: source | derived | preview
  derived_from: asset_id | None
  via: {engine, engine_version, op, policy} | None

Page
  id, size: (w, h) pt
  source: {asset: asset_id, index: int}   # page/slide/artboard inside the asset
  preview: asset_id | None                # single-page PDF (role=preview)
  frames: [Frame]                         # in memory only; empty in the MVP

Frame                           # discriminated on `kind`; filled by later engines
  id, kind: text | vector | image | media | group
  bbox: (x, y, w, h) pt, rotation: deg
  asset: asset_id | None, text: str | None, children: [Frame], time: (start_s, end_s) | None

Media
  id, asset, kind: video | audio, duration_s
```

Product mapping: DeckCraft slides, VectorCraft artboards (a multi-page PDF imports as one artboard
per page, ✓), DesignCraft pages and PdfCraft pages all become a `Page`. A PhotoCraft image has no
pages and becomes one implicit page.

## 3. `.mcruft` package

```text
Talk.mcruft/
  manifest.json            # the only file mcruft must understand
  assets/                  # native files, write-once: deck.pptx, poster.vectorcraft, scan.pdf, photo.psd
  derived/                 # outputs of mcruft operations (provenance in the manifest)
  previews/page-0000.pdf   # optional single-page PDF per page (Keynote-style thumbnails)
```

`manifest.json`, schema_version 1:

```json
{
  "schema_version": 1,
  "generator": "mcruft 0.1.0",
  "meta": {"title": "Talk", "created": "2026-10-25T12:00:00Z", "modified": "2026-10-25T12:00:00Z"},
  "assets": {
    "a1": {"path": "assets/deck.pptx", "media_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "sha256": "…", "role": "source"},
    "p0": {"path": "previews/page-0000.pdf", "media_type": "application/pdf", "sha256": "…", "role": "preview",
            "derived_from": "a1", "via": {"engine": "deckcraft-cli", "engine_version": "0.10.0", "op": "export_pages", "policy": "editable"}}
  },
  "pages": [
    {"id": "pg0", "size": [960, 540], "source": {"asset": "a1", "index": 0}, "preview": "p0"}
  ],
  "media": []
}
```

Rules:

- **Write-once assets.** `add_file` copies the file into `assets/` once. If the name is taken, it
  appends `-1`, `-2`, and so on. Saves never rewrite assets. Only `manifest.json` is written, via
  a temporary file and `os.replace`, which is atomic. Saving to a new path copies the referenced
  assets there.
- **Trust boundary on load.** Paths must be relative POSIX paths that stay inside the package after
  resolution. Absolute paths, `..`, and symlinks are rejected (`PackageError`). An unknown
  `schema_version` raises `UnsupportedSchema`.
- **Hashes.** `sha256` is checked on load. A mismatch is a warning, because the user may have
  edited the asset in its own app. `doc.refresh()` recomputes hashes and drops stale previews.
- **Frames are not persisted** in v1; they are recomputed by inspection.
- Paths passed to CLIs are absolute, so a filename starting with `-` is never read as a flag.

## 4. Engines and routing

An engine wraps one backend and declares capabilities:

```text
Capability(op, src, dst, policy, verified_with: "<engine> <version>" | None, note)
backend kinds: cli | mcp | native | lib
ops: convert, export_pages, outline_text, build_deck, extract_pages, combine   (+ Engine.inspect(path))
```

- `convert` turns a whole file into another format.
- `export_pages` writes selected 0-based pages (`opts["pages"]`) into one PDF, or into one PNG
  per page named `stem-NNNN.png` (`opts["dpi"]`).
- `outline_text` is the VectorCraft pass in §5.1.
- `build_deck` places PNGs on blank slides (DeckCraft).
- `extract_pages` and `combine` are PDF page operations (lib: pypdf).
- Composite routes (fidelity via the outline pass, pages → deck) live in the core, so no product
  engine depends on another.

- Routing picks, among the engines that are available and declare the capability: verified ones
  first, then the backend order `native > lib > cli > mcp`. `engine="…"` pins a choice. `lib`
  capabilities count as verified when a unit test covers them.
- Engines register through the entry-point group `mcruft.engines`. The core registers its `lib`
  engine; each `mcruft_<product>` package registers its product engine.
- CLI binary lookup: `$MCRUFT_<PRODUCT>_CLI`, then the `mcruft_<product>_bin` package (bundled,
  §9), then `PATH`. A missing binary marks the engine unavailable. A version older than the
  declared `min_version` adds a warning to the Report.
- **MCP** (`[mcp]` extra, official `mcp` Python SDK): `engine.session()` opens
  `<product>-cli mcp` over stdio, with `--automation-read-root` and `--automation-write-root` set
  to the package and temp dirs (VectorCraft also gets `--headless`). It exposes `call(tool, args)`.
  It is for interactive multi-step work; no MVP route depends on it. The MVP has one smoke test.

### Inspect (how pages are discovered)

| Format | Engine | Pages, size |
|---|---|---|
| pdf | lib: pypdf | page count, MediaBox |
| pptx | lib: python-pptx | slide count, slide size |
| svg | lib: XML `viewBox`/`width`/`height` | one page |
| png, jpg | lib: Pillow | one page, px → pt via DPI |
| vectorcraft, ai | cli: `vectorcraft-cli info` | artboards |
| psd, pcraft | cli: `photocraft-cli info` | one page |
| idml, designcraft | cli: `designcraft-cli run --in X --cmd document.inspect` | pages |

## 5. Conversion and export matrix (MVP)

| Route | `editable` | `fidelity` |
|---|---|---|
| pptx → pdf | ✓ deckcraft `convert`: text selectable, fonts embedded; Loss `raster` (slide art rasterised) | ✓ deckcraft export, then VectorCraft outline pass (§5.1): no font dependency; Loss `layout` |
| pptx → png | ✗ raster is not editable | ✓ deckcraft `convert` / `run --export` per slide |
| pptx → single-slide pdf | ✓ deckcraft `run --export x.pdf --export-params {"slides":[i]}` | same + outline pass |
| pptx ↔ deckcraft | ✓ deckcraft `convert` | ✗ (same route; use editable) |
| svg → pdf | ✓ vectorcraft `convert` (fonts embedded) | ✓ vectorcraft `run … type.createOutlines --export` (no fonts) |
| svg → png | ✗ | ✓ vectorcraft `convert`; ~ lib resvg-py |
| pdf → svg | ✓ vectorcraft `convert` (text stays `<text>`) | ✓ vectorcraft `run … type.createOutlines --export .svg` |
| pdf → png | ✗ | ✓ pdfcraft `render --page N`; ~ lib pypdfium2 |
| pdf → pdf (outlined) | n/a | ✓ outline pass, 1-page and 4-page inputs |
| pdf → psd | ✗ layers not rebuilt | ✓ vectorcraft `convert` |
| png → pdf | as fidelity (an image has no structure to keep, so both policies use the same route; no Loss) | ✓ photocraft `convert` |
| png ↔ psd, psd → pcraft | ✓ photocraft `convert` | same |
| png/jpg page → png (`export_pages`) | ✗ | ✓ lib: Pillow (RGBA; ICC profile not kept, reported as Loss `effects`) |
| any page → png (`export`, `render`) | ✗ raster targets accept only `fidelity`; `policy="editable"` raises `UnsupportedRoute` | ✓ per-source route |
| idml/designcraft → pdf, png, pptx | ~ designcraft `run --in --export` (✓ from `--sample` only) | ~ same + outline pass |
| pages → pptx deck | ✗ no verified pdf→editable-slide route | ✓ render pages to PNG, deckcraft `run` with blank slides + full-bleed `insert.picture` |
| extract / combine pdf pages | ✓ lib: pypdf | same |

### 5.1 Outline pass

The pass runs `vectorcraft-cli run --in in.pdf --cmd select.all --cmd type.createOutlines --export
out.pdf`. It is verified for 1-page and 4-page PDFs (no `/FontFile` remains). Because VectorCraft
re-imports the PDF, the Report always adds `Loss(kind="layout", detail="re-imported via
VectorCraft: links, annotations and forms may be dropped")` and passes VectorCraft's warnings
through, for example CMYK conversion of RGB images.

### 5.2 Document export pipeline

`doc.export(path, policy=…)` over pages from several assets proceeds as follows:

1. Group consecutive pages by source asset.
2. Export each asset's pages to PDF. mcruft tries, in order:
   - `export_pages` with the requested policy;
   - `export_pages` with the editable policy (the fidelity variant is the outline pass in step 5);
   - for single-page sources, `convert` to PDF.

   Raster sources (png, jpg, psd, pcraft) use their only route, which is fidelity, for both
   policies (see the png → pdf row).
3. Extract the needed page indexes (pypdf).
4. Combine in document order (pypdf) into a temporary file in the target directory.
5. If `fonts="outline"`, run the outline pass on the result.
6. Move the result onto the target with `os.replace`. A failed export leaves no file at the
   target. A target path that is one of the document's assets is refused (`PackageError`).
   `Page.render` and PNG export write through a temporary directory and never touch other files
   next to the target.

`policy="fidelity"` implies `fonts="outline"` and `policy="editable"` implies `fonts="embed"`.
The caller may override `fonts`. A `.png` target writes `stem-0000.png`, and so on, one per page;
a `.pptx` target uses the pages → deck route.

## 6. Python API (MVP)

```python
import mcruft

doc = mcruft.open(path)                       # .mcruft folder, or any inspectable file (1-asset doc, unsaved)
doc = mcruft.new(title="Talk")
doc.add_file(path) -> list[Page]              # copies the file in on save; appends its pages
doc.remove_pages(indexes); doc.move_page(i, to)
doc.split() -> list[Document]                 # manifest-level: one doc per page, sharing asset files
mcruft.merge(docs) -> Document                # manifest-level concatenation
doc.save(path=None, previews=False) -> Report # previews = single-page PDFs via the editable export (fonts embedded, no outline pass)
doc.refresh() -> Report

doc.export(path, *, policy, pages=None, fonts=None, dpi=150) -> Report      # .pdf, .png, .svg (1 page), .pptx
mcruft.convert(src, dst, *, policy) -> Report
# Without a convert capability, use export_pages at the same policy: multi-page PNG outputs are stem-NNNN.png; a single page writes exactly dst.
mcruft.convert_editable(src, dst) -> Report   # == convert(policy="editable")
mcruft.convert_fidelity(src, dst) -> Report   # == convert(policy="fidelity")
page.render(path, dpi=150) -> Report          # always fidelity

mcruft.engines() -> list[EngineInfo]          # name, kind, available, version, capabilities

Report: op, policy, engine, engine_version, outputs: list[Path], losses: list[Loss], warnings: list[str]
Loss: kind ("raster"|"fonts"|"layout"|"effects"|"media"|"unsupported"), detail, page: int | None
```

Errors: `McruftError` → `UnsupportedRoute`, `EngineUnavailable`, `EngineFailed` (non-zero exit;
includes the stderr tail and the command line), `UnsupportedSchema`, `PackageError`.

## 7. Round trip to a specialist engine

MVP: **page-level only.** `with page.edit_in("photocraft") as path:`

1. Produces a working file that the engine can edit.
   - If the engine natively reads the source asset's format (DeckCraft: pptx/deckcraft;
     PhotoCraft: png/jpg/psd/pcraft; VectorCraft: svg/ai/vectorcraft/pdf; PdfCraft: pdf;
     DesignCraft: idml/designcraft), the working file is a copy of the whole asset, and the page
     keeps its index.
   - Otherwise the page is converted once, with the **editable** policy, to the engine's format:
     PhotoCraft gets `.psd`, VectorCraft `.vectorcraft`, PdfCraft a single-page `.pdf`. The page
     index becomes 0.
   - If no editable route exists, mcruft raises `UnsupportedRoute`. It never hands over a
     rasterised picture as an "editable" page.
2. Yields the path for the caller (CLI, MCP session or GUI) to edit.
3. On exit, if the hash changed, adds the file as a `derived` asset with provenance and points
   `page.source` at it. Later exports use the edited asset, and the preview is dropped.

Frame-level write-back into the original asset (placing edited content back with
`insert.picture`, `file.place` or `page_add_image`) is designed but deferred.

## 8. Time-based media (batch 2)

The MVP stores video and audio files as `Media` assets. Planned operations, using FilmCraft,
EffectCraft and SoundCraft:

- `media.keyframes_to_pages(times)`: still renders become image pages.
- `doc.pages_to_keyframes()`: page renders become a video timeline.
- Media frames embedded on slides.

## 9. Repository and distributions

```text
packages/mcruft/                 core (model, package I/O, router, Report, lib engine, CLI + MCP runners)
packages/mcruft_<product>/       ×5: engine declaration + command adapters (pure Python, entry point)
native/mcruft_pdfcraft_native/   maturin/PyO3 proof binding; NOT a uv workspace member
tools/bundle_cli.py              builds the mcruft-<product>-bin wheels
```

- **Distributions.**
  - `mcruft` (pure). This is the metapackage: `mcruft[engines]` pulls in the five
    `mcruft-<product>` packages, and `mcruft[mcp]` adds the MCP SDK.
  - `mcruft-<product>` (pure, `py3-none-any`), each with a `[bundled]` extra that pulls in
    `mcruft-<product>-bin`.
  - `mcruft-<product>-bin`, a separate distribution: a platform wheel containing
    `mcruft_<product>_bin/bin/<product>-cli`, thinned to one architecture, plus the product's
    LICENSE and ATTRIBUTION and a NOTICE.
  - The MVP builds `macosx_11_0_arm64` only. The arm64 VectorCraft wheel is about 54 MB, under
    PyPI's 100 MB default file limit; a universal one would not be.
- **Native binding.** Pin every crate from one repo to the commit of the release tag that matches
  the installed CLI. Link only model, format, render and pdf-level crates. Copy only the `hayro`
  and `lopdf` `[patch.crates-io]` entries. The proof binding covers PdfCraft page count, extract
  and combine. It is built on demand (`maturin build`), not by `uv sync`.
- **Publishing.** The MVP is published on GitHub only. PyPI uploads need an explicit owner
  decision.

## 10. Out of scope for the MVP

- Batch-2 products.
- Library engines beyond pypdf, python-pptx and Pillow. pypdfium2 (pdf → png), resvg-py
  (svg → png) and psd-tools (PSD layers) were selected in `docs/research/native-libs.md`, but are
  not wired in yet. Their routes are marked "~" in §5. The first to add is pypdfium2 pdf → png,
  which removes a CLI dependency.
- Text editing: the planned `frame.set_text(str)` routes to DeckCraft `text.set` and DesignCraft
  `story.setText`.
- Frame-level write-back.
- Populated `frames`.
- A layout engine.
- Zipped packages.
- x86_64, Linux and Windows binary wheels.
- MCP-driven GUI automation.
- Faithful Office rendering outside the ArtCraft engines.
