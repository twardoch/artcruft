---
this_file: docs/research/products/designcraft.md
---

# DesignCraft

Evidence key: **[CLI]** = `designcraft-cli` 0.12.0 help/run; **[MCP]** = live `tools/list`; **[src]**; **[unverified]**.

## Purpose and reference product

Page-layout and publishing app (Adobe InDesign clone; target InDesign 2026 / 21.6). Repo `storytold/designcraft`, `MIT OR Apache-2.0`. Git HEAD `a930276fd7462f3d9abd2fbb38544c94c0c911c8` (2026-10-15). Workspace 0.8.0 vs installed CLI 0.12.0 (version skew, README.md).

## Native file format

`.designcraft` [src: `crates/format`, file-format-parity.md]: ZIP with `document.json` plus embedded assets; versioned. Model (`designcraft-doc`): spreads, pages, parents (master pages), layers, frames, stories (text is separate from frames and can be threaded), styles, swatches. `file.openBytes` also accepts "DesignCraft JSON". Default Letter page 612x792 pt; coordinates are spread space, y down. Asset loading is indexed by content hash [src].

## Readable / writable formats

- Open [CLI `file.open`/`file.openIdml` text]: `.designcraft`, IDML, and InDesign `.indd`/`.indt` (converted to IDML first; conversion warnings are returned). **Conflict:** `docs/file-format-parity.md` (reviewed 2026-10-10) still says `.indd` is unsupported (gap 2). The CLI help text is newer; I did not open a real `.indd`, so treat it as **unverified**.
- Place [CLI `file.place`]: PNG, JPEG, GIF, WebP, TIFF, BMP, PSD, SVG; PDF pages (`pdfPage`, `pdfCrop`); `.txt`, `.docx`, `.rtf`, `.md` into text frames; `.xlsx` as a table; video/audio.
- Write [CLI command ids]: `.designcraft` (`file.save/saveAs/saveACopy`), IDML (`file.exportIdml`), PDF (`file.exportPdf`), EPUB 3 reflowable and fixed (`file.exportEpub/exportFixedEpub`), HTML (`file.exportHtml`), editable PPTX (`file.exportPptx`), text/RTF/tagged (`file.exportText`), XML (`file.exportXml`), PNG/JPEG via `run --export x.png` and MCP `export_png`/`render_page` [src: JPEG CLI only]. Book export: `book.exportPdf`.
- PDF [CLI `file.exportPdf` params]: pages range, flatten, spreads, bleed, marks, `standard: none|x4|a2b`, `tagged`, `compressImages`, interactive options. Text is real text with **embedded font subsets**; the param list has **no outline-text option** (verified). Ran `designcraft-cli run --sample --export p.pdf --export p.png`: 4-page 552 KB PDF and a 630x810 PNG of page 1 (use `--page N` / `--all-pages DIR` for others).
- **No SVG export** [src: file-format-parity.md].

## CLI surface [CLI]

Subcommands: `run`, `commands [FILTER]`, `describe CMD`, `script [FILE|-]`, `app`, `mcp`, `perf`, `bench`, `links`, `--version`.
- `run [--in FILE | --sample] [--cmd ID[=JSON]]... [--page N] [--scale S] [--pdf-options JSON] [--export OUT] [--all-pages DIR]`: `--page/--scale/--pdf-options` apply to the exports that follow them. Output is human text (`wrote /tmp/p.pdf (4 pages, 552552 bytes)`), not JSON per step. Failure: `designcraft-cli: unknown command ...`, exit 1 (verified).
- `script [FILE|-] [--in FILE | --sample] [--connect PORT] [--save OUT] [--export OUT] [--keep-going]`: script of commands (format not inspected); `--keep-going` is the only CLI in the set with an explicit continue-on-error switch.
- `app [--port PORT] COMMAND [JSON]`: send a command to a running GUI. `mcp [--connect PORT] [--sample] [--automation-read-root DIR] [--automation-write-root DIR]` (roots conflict with `--connect`).

## Command catalogue [CLI `commands`, counted]

527 commands (JSON). Groups: object 59, type 43, table 40, file 35, style 28, layout 26, edit 18, text 16, path 14, swatch 13, transform 10, book 10, guide 10, xml 10, data 10. Key ids:
- `file.new {preset, pages, facingPages, margins, bleed, slug, columns, ...}`, `file.open`, `file.openIdml`, `file.save`, `file.exportPdf`, `file.exportIdml`, `file.exportPptx`, `file.package {dir, idml, pdf}`, `file.place {path|base64, frame, x, y, width, pdfPage, ...}`.
- Pages: `layout.pages.insert {count, after, parent}`, `layout.pages.delete {pages}`, `layout.pages.move {from,to}`, `layout.pages.duplicateSpread`, `layout.pages.applyParent`, `layout.pageSize`, `layout.pages.toSpread`, `layout.parents.new/delete`, `layout.createAlternate` (liquid layout copies at another size).
- Frames/text: `frame.create {rect:[x0,y0,x1,y1], shape, content: graphic|text|unassigned, text}`, `story.setText`, `story.replaceRange`, `story.placeAndLink`, `document.inspect`.
- Index base is mixed [CLI param docs]: `file.exportPdf pages`, `layout.pageSize pages`, `layout.selectPage` are 1-based; `layout.removeOverrides page` and `layout.pages.duplicateSpread` result are 0-based; `layout.pages.insert/delete/move` just say "page index" (base not stated, unverified). A unified API must normalise.

## MCP surface [MCP]

`designcraft-cli mcp` (0.12.0), 26 tools: `list_commands`, `execute`, `batch`, `inspect_document`, `get_story`, `set_story_text`, `new_document`, `open_document`, `save_document`, `place_image`, `render_page`, `export_png`, plus GUI-driving tools (`select_tool`, `pointer`, `key`, `type_text`, `ime`, `click`, `drag`, `menu_list`, `ui_inspect`, `ui_set`, `dialog_set/confirm/cancel`, `screenshot`). No dedicated PDF export tool: PDF export goes through `execute file.exportPdf`. Source: `crates/mcp`.

## Rust crates (17 in `crates/`)

| crate | role | bindable as library? | notable deps |
|---|---|---|---|
| doc | model: spreads, pages, parents, frames, stories, styles | yes | serde |
| format | `.designcraft` zip + JSON | yes | zip |
| idml | IDML import/export | yes | quick-xml, zip |
| pdf | PDF export (krilla): subsets, CMYK/spot, bleed, marks, PDF/X-4, A-2b | yes (needs craft-libs `craft-pdf`) | craft-pdf, krilla-svg, hayro-syntax |
| render | page to pixels | yes | vello_cpu, hayro |
| compose | Knuth-Plass composer, hyphenation, columns, threading, wrap | yes | hypher, regex |
| fonts, images, color, geom | font db, placed-graphic decode (raster+SVG), colour, geometry | yes | skrifa, resvg, moxcms |
| epub, pptx, textimport | EPUB 3, PPTX export, txt/docx/rtf import | yes | zip, quick-xml |
| engine | session, history, command registry | yes, but heavy | craft-print (system spooler) |
| tools, mcp, ui-egui | pointer tools, MCP server, GUI | no | egui |

No PyO3 in the repo.

## Operations relevant to mcruft

| operation | route |
|---|---|
| page add/remove/reorder | `layout.pages.insert/delete/move/duplicateSpread` (pages live in spreads; facing pages) |
| PDF with embedded fonts | `file.exportPdf` (always subsets) |
| PDF with outlined fonts | not offered (verified from param list) |
| export PNG | `run --export x.png [--page N] [--scale S]`, `--all-pages DIR`, MCP `export_png`/`render_page` |
| export SVG | none |
| import PDF | not as a document; `file.place` places a PDF page as a graphic (`pdfPage`, `pdfCrop`) |
| place image | `file.place`, MCP `place_image` |
| text frame edit | `frame.create {content:"text", text}`, `story.setText`/`replaceRange`, MCP `get_story`/`set_story_text` |
| single-page PDF | `file.exportPdf {pages:"2"}` |

## Known gaps vs InDesign [src: docs/gaps.md]

Alpha blocker: primary text frame autoflow adds undeletable pages. Blocking: basic editing failures, `.indd` reliability, IDML round trip unproven on real files, composition not compared with InDesign, startup crashes on some GPUs, installed fonts not always found, no PR CI. High: PDF presets, printing, style editing, tables. Self-scored ~40% format readiness.
