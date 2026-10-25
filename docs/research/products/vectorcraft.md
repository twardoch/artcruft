---
this_file: docs/research/products/vectorcraft.md
---

# VectorCraft

Evidence key: **[CLI]** = ran/read `vectorcraft-cli` 0.16.0; **[MCP]** = live `tools/list` over stdio (`mcp --headless`); **[src]** = repo source/docs; **[unverified]** = claimed, not checked.

## Purpose and reference product

Vector illustration app (Adobe Illustrator clone). Repo `storytold/vectorcraft`, `MIT OR Apache-2.0`, Rust edition 2024, rust 1.95. Git HEAD `b12a52f7249e0aa73f030587e05ed9ce0c73ab67` (2026-10-14). The installed CLI reports 0.16.0 while the checkout's workspace version is 0.11.0 (see README.md "Version skew").

## Native file format

`.vectorcraft` [src: `crates/format/src/lib.rs`]: UTF-8 JSON, optionally gzip-compressed (detected by magic bytes). Envelope: `format`, `version` (currently v4), `generator`, optional `preview` (PNG, base64), `profiles` (ICC), `pdf` (optional embedded PDF of all artboards), `document` (the `vectorcraft-doc` model), `images` (base64). Large images go after the JSON behind a `\n\0VCBLOBS\0` marker (v4). Unknown data is kept in `document.unknown`. Linked images may be stored as low-res proxies. Also `.vctemplate`.

## Readable / writable formats [CLI help text]

- Read: .vectorcraft .drawcraft .svg .svgz .pdf .ai .ait .png .jpg .jpeg .gif .webp .tif .tiff .bmp .tga .vda .icb .vst .psd .psb .vctemplate .dxf .emf .wmf .eps .epsf .ps .af .afdesign .afpub
- Write: .vectorcraft .svg .svgz .pdf .ai .png .jpg .gif .webp .tif .bmp .vctemplate .txt .dxf .eps .emf .wmf .tga .psd
- `.ai` is written PDF-compatible only (no Illustrator private data) [src: file-format-parity.md]. PDF opens as editable vector art [CLI: `file.open`, `file.place` "a PDF/.ai page"].
- I did not round-trip any of these; fidelity is whatever the docs claim.

## CLI surface [CLI]

`vectorcraft-cli` subcommands: `mcp`, `run`, `commands`, `convert`, `info`, `bench`, `perf`.
- `run [--in FILE] [--cmd ID [--params JSON] | --commands FILE|-]... [--export FILE]... [--scale N]`: headless batch; steps in order; one JSON line per step on stdout (`{"command":..,"result":..,"step":"cmd"}`, `{"result":{bytes,format,path,warnings},"step":"export"}`). `--commands` accepts a JSON array or JSON Lines of `{"command"|"id", "params"}` (max 100000 steps). Failure: stderr `vectorcraft-cli: step N (id): unknown command ...`, exit 1 (verified).
- `convert IN OUT [--scale N] [--artboard I | --range R] [--outline-text] [--decimals N] [--replace-lossy] [--editing-data] [--ai-version 7|pdf] [--hidden-objects ..] [--transparent-images ..]`; refuses OUT==IN when reading dropped content unless `--replace-lossy`. Output carries `warnings` and `importWarnings`.
- `info FILE` prints JSON (import warnings, colour mode, units, artboards, object counts, fonts).
- `commands` prints the catalogue as JSON.

## Command catalogue [CLI `commands`, counted]

802 commands. Largest groups: object 141, select 50, path 33, document 32, edit 30, text 29, file 28, layer 26, perspective 25, swatch 23, type 23, paint 22. Key ids:
- Open/save: `file.new`, `file.open {path}`, `file.save`, `file.saveAs`, `file.saveCopy`, `file.close`, `file.package`.
- Export: `document.export {path, format, artboard|artboards|range, selectedOnly, ppi|scale, background}`, `document.exportPdf {preset, standard: none|pdfA2b|pdfX1a|pdfX3|pdfX4, compatibility, advanced.outlineText, ...}`, `document.exportForScreens`, `document.exportEps`, `document.exportDxf`.
- Artboards (the page concept): `artboard.new {x,y,width,height,name}`, `artboard.delete {index|indices}`, `artboard.duplicate`, `artboard.reorder {index,to}`, `artboard.setProps`, `artboard.move`, `artboard.fitToArt`, `artboard.rearrange`.
- Place: `file.place {path|dataBase64, link, at, rect, replace, page, crop, textAs}` (images, PDF/.ai pages, .txt as area type).

## MCP surface [MCP]

`vectorcraft-cli mcp --headless` (server name `vectorcraft`, 0.16.0), 32 tools: generic `command_list/command_run/command_batch` (aliases `list_commands/run_command`), `doc_inspect`/`inspect_document`, `render_preview`, `open_file`, `save_file`, `export`, `add_text`, `draw_path`, `draw_shape`, `set_paint`, `transform`, `pathfinder`, `apply_effect`, `create_graph`, `text_wrap`, `undo/redo`, plus GUI-driving tools (`pointer_gesture`, `press_key`, `type_text`, `invoke_menu`, `open_panel`, `select_tool`, `screenshot`, `ui_inspect`, `ui_screenshot`, `inspect_ui`). Resources: `vectorcraft://object/{id}`, `/command/{id}`, `/effect/{id}`, `/swatch/{name}`. Without `--headless` it first tries a running GUI on 127.0.0.1:7979. `--automation-read-root/--automation-write-root` confine file access and imply headless.

## Rust crates (24 in `crates/`, plus 3 apps)

| crate | role | bindable as library? | notable deps |
|---|---|---|---|
| doc | document model (artboards, layers, objects, appearance; pure data + serde) | yes | kurbo, serde, image, tiff |
| format | native `.vectorcraft` read/write | yes | serde_json, flate2 |
| geom, color | geometry, colour (ICC via moxcms) | yes | kurbo |
| svg | SVG import/export | yes | usvg, svgtypes |
| pdf | PDF import/export | yes | craft-pdf, skrifa, aes, sha2 |
| render | doc to pixels | yes | vello_cpu |
| text | font db, shaping, layout | yes | skrifa, harfrust, icu_segmenter |
| pathops, trace, brush, effects, three-d | booleans, image trace, brushes, live effects, 3D | yes | linesweeper |
| eps, metafile (EMF/WMF), cad (DXF), affinity | extra formats | yes | - |
| engine | sessions, history, command registry (links nearly everything) | yes, but heavy | wasmi (via plugins), scriptcheck |
| mcp | MCP server | no | - |
| plugins | wasmi WASM plug-in host | no (not needed) | wasmi |
| tools | pointer state machines | no | - |
| ui-egui | GUI | no | egui |
| scriptcheck, testkit | script checker, tests | no | proptest |

No PyO3/uniffi in the repo (`vectorcraft-web` uses wasm-bindgen only).

## Operations relevant to mcruft

| operation | route |
|---|---|
| page add/remove/reorder | artboards: `artboard.new/delete/reorder/duplicate`; indices 0-based in commands, 1-based in `range` strings |
| export PDF, fonts embedded | `document.exportPdf` default: embedded subsets, real text (`advanced.outlineText: false`) |
| export PDF, fonts outlined | `document.exportPdf {advanced:{outlineText:true}}`; SVG: `convert --outline-text`. **The only one of the five products with an explicit outline-text switch.** |
| export PNG / SVG | `document.export {format:png|svg, artboard, ppi|scale}`; one file per artboard for SVG/raster |
| import PDF | `file.open x.pdf` (editable art) or `file.place` (linked, drawn as vectors unless `textAs:"outlines"`) |
| place image | `file.place {path, at|rect, link}` |
| text frame edit | `add_text` (MCP), `text.*`/`type.*` commands; area vs point type [unverified: exact ids not exercised] |
| single-page PDF preview | `document.exportPdf {artboard:N}` |

## Known gaps vs Illustrator [src: docs/gaps.md]

Interaction fidelity, real-world `.ai`/EPS files, launch stability on real machines, advanced type, brushes/symbols/libraries, 3D/Materials, raster effects/Effect Gallery, scripting (no JS/AppleScript parity; `scriptcheck` only statically checks scripts). `.ai` write lacks Illustrator editing data. Frame/page concept is free artboards on a pasteboard, not an ordered page list.
