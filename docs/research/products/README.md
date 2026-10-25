---
this_file: docs/research/products/README.md
---

# Batch-1 product comparison

Source of every cell: the per-app docs in this folder (CLI help, live MCP `tools/list`, command catalogues, repo source and docs). "Verified" means I ran or read it; docs claims that I did not run are marked in the per-app files. Researched 2026-10-25.

## Matrix

| | VectorCraft | DeckCraft | PhotoCraft | PdfCraft | DesignCraft |
|---|---|---|---|---|---|
| Reference product | Illustrator | PowerPoint | Photoshop | Acrobat Pro | InDesign |
| Native format | `.vectorcraft` (JSON, gzip optional, base64 or blob images) | `.deckcraft` (zip: JSON + media) | `.pcraft` (zip or dir: manifest + zstd tiles) | PDF | `.designcraft` (zip: document.json + assets) |
| Page-like unit | artboard (0-based, free on pasteboard) | slide (0-based, has id) | none (artboards, layer comps) | page (1-based) | page in spread (mixed bases) |
| Reads | svg, pdf, ai, eps, psd, png/jpg/..., dxf, emf/wmf, Affinity | deckcraft, pptx, md/txt outline | psd/psb, tiff, ora, pdn, kra, svg, flat rasters, raw, heic | pdf; images/txt to pdf | designcraft, idml, indd (unverified); places images/pdf pages/docx/rtf/md/xlsx |
| Writes | vectorcraft, svg, pdf, ai, eps, dxf, emf/wmf, png/jpg/gif/webp/tif/bmp/tga, psd | deckcraft, pptx, pdf, png/jpg, gif, md/txt | pcraft, psd/psb, tiff, ora, flat rasters; pdf (raster only) | pdf, pdf/a, png/jpg/tif, docx/pptx/html/rtf, txt | designcraft, idml, pdf (X-4, A-2b), epub, html, pptx, txt/rtf, png |
| Export PDF | yes, per artboard range | yes, art rasterised | raster only | native | yes, real text |
| PDF fonts embedded vs outlined | **both** (`advanced.outlineText`) | embedded only | n/a | n/a (as-is) | embedded only |
| Export PNG | yes | yes | yes | yes (pages) | yes (per page) |
| Export SVG | yes | no | no | no | no |
| Import PDF as editable | yes (vector art) | no | no | native | no (placed graphic only) |
| Place image | `file.place` | `insert.picture` | `file.placeEmbedded/Linked` | `page_add_image` | `file.place` |
| Text edit | text objects | shape text (`text.set`) | type layers | `page_add_text`, fragile edit | frame + story (`story.setText`) |
| Page add/remove/reorder | artboard.* | slide.* | no | page_* | layout.pages.* |
| Command count (installed CLI) | 802 | ~321 | 935 | 175 tools | 527 |
| CLI batch | `run --cmd/--commands/--export` (JSON lines) | `run --cmd id=json --save` (stops on first error, saves nothing) | `run`, `batch` (folder), `droplet`, `serve` (JSON lines) | `run --script`, `batch --steps` | `run`, `script` (`--keep-going`) |
| CLI structured output | JSON per step | text (`--print`) | JSON per command | JSON/text | text |
| MCP tools (live) | 32 | 25 | 25 | 175 (compact mode available) | 26 |
| MCP generic command tool | yes | yes | yes | yes (`command_run`, `tool_call`) | yes (`execute`) |
| Bindable engine crates | doc, format, svg, pdf, render, text, pathops... | model, format, pptx, pdf, render, text | doc, format, io, psd, codecs, compose, vector | cos, model, organize, edit, create, render, export | doc, format, idml, pdf, render, compose |
| `-engine` crate heavy? | yes (wasmi plugins) | yes (media codecs) | yes (craft-print, rayon) | yes (ocr, js, sign) | yes (craft-print) |
| Existing Python binding | none in repo; DeckCraft/PdfCraft via pydoccraft (extraction only) | pydoccraft (read/render/convert) | none | pydoccraft | none |
| Repo HEAD (local) | `b12a52f7` 2026-10-14 | `9859da39` 2026-10-14 | `4e7a17cd` 2026-10-15 | `dc41044b` 2026-10-15 | `a930276f` 2026-10-15 |

All five repos are `MIT OR Apache-2.0`, Rust edition 2024, rust 1.95. `craft-libs` (`8f5a2831614e632f91ad367f7af2a6e5b61b9529`, 2026-10-15) holds shared `craft-pdf` (hayro + krilla), `craft-cms`, `craft-print`, `craft-settings`, `craft-ui`, `craft-atomic`, `craft-quit`; DeckCraft, DesignCraft and VectorCraft PDF crates depend on `craft-pdf`.

## Version skew (must be resolved before pinning)

Installed CLI versions and local checkouts disagree: VectorCraft CLI 0.16.0 vs workspace 0.11.0; DeckCraft 0.10.0 vs 0.7.0; PhotoCraft 0.15.1 (built from commit 60c87b988, 2026-10-23) vs checkout 0.9.0 HEAD dated 2026-10-15; PdfCraft 0.13.0 vs 0.8.0; DesignCraft 0.12.0 vs 0.8.0. artcraft-in-a-box pins release tags v0.16.0 / v0.15.1 / v0.12.0 for the same apps. So either the workspace `version` field lags the release tags, or the checkouts are behind. All CLI facts here describe the installed binaries; crate facts describe the local checkouts. I did not fetch from the network.

## Cross-app observations for a Document -> Page -> Frame API

1. **Every product is "a command registry plus JSON params".** Each exposes the whole app as `id + JSON` through `run`/`execute`/`command_run`. A generic `call_command(id, params)` escape hatch is cheap everywhere, but ids and flag shapes differ per app (`file.save` vs `doc_save`, `--cmd id=json` vs `--cmd id --params json`), so the unified layer needs an adapter per product.
2. **Page concept is not uniform.** Illustrator-style artboards (free-floating, no ordering semantics), slides (ordered, with ids), spread pages (facing pairs, parents), PDF pages, and raster documents with no pages at all. Model `Page` as optional/derived for PhotoCraft (one implicit page, artboards as extra pages is a lossy choice).
3. **Index bases and rect conventions clash.** 0-based (artboards, slides) vs 1-based (PDF, DesignCraft exports); DeckCraft rects `[x,y,w,h]`, DesignCraft rects `[x0,y0,x1,y1]`, PhotoCraft in pixels, others in points, all y-down in the command layer. The unified API should fix one convention and convert at the adapter.
4. **Frame vs story.** DesignCraft separates text frames from threaded stories; DeckCraft/VectorCraft attach text to the object; PhotoCraft has type layers; PdfCraft has content-stream text runs (editing existing runs is fragile). A `TextFrame` should carry geometry and a reference to text content, not embed it.
5. **Font policy cannot be uniform.** Only VectorCraft can write outlined text (PDF and SVG). DeckCraft and DesignCraft always embed subsets; PhotoCraft's PDF is raster. For the spec's "visual fidelity" conversion variant, report `outline_fonts` as unsupported for four of five routes rather than faking it.
6. **Fidelity and editability variants differ by route.** DeckCraft PDF rasterises slide art (fidelity is fine, text layer still searchable); PhotoCraft PDF is raster-only; VectorCraft is the only importer of PDF as editable art. Round trips must be measured; docs here do not prove them.
7. **Native assets differ.** `.pcraft` and `.designcraft` are content-addressed/zipped; `.vectorcraft` inlines base64 or trailing blobs; `.deckcraft` zips media. Referencing native assets from a `.mcruft` package means storing the native file as an opaque member plus a preview, not translating it.
8. **Rust bindability is real but no product ships Python bindings.** Use the model/format/pdf/render crates, avoid `*-engine` (drags in codecs, wasmi, OCR, JS, print spoolers) unless command-level editing is required; pydoccraft proves the pattern for DeckCraft/PdfCraft. Command-level editing in-process needs an engine crate and is the expensive path.
9. **Subprocess CLI is the lowest-friction route to command-level editing** (all five have headless `run`), but bundling five 120-200 MB binaries per wheel conflicts with small wheels; the CLI binaries are not source-built here. Decide per product: in-process crates for read/render/convert, CLI or engine crate for edits.
10. **MCP is not a stable contract.** Tool counts and names differ (25-175), PhotoCraft's server uses a different stack, and GUI-driving tools are mixed in with document tools. Treat MCP as a discovery aid and the command catalogue as the real surface; pin the product revision because the catalogues are large and change weekly.
