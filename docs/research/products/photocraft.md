---
this_file: docs/research/products/photocraft.md
---

# PhotoCraft

Evidence key: **[CLI]** = `photocraft-cli` 0.15.1 (build 60c87b988, 2026-10-23); **[MCP]** = live `tools/list`; **[src]** = repo docs/source; **[unverified]**.

## Purpose and reference product

Raster image editor with layers, masks, adjustment layers, type, vectors, PSD (Adobe Photoshop clone). Repo `storytold/photocraft`, `MIT OR Apache-2.0`. Git HEAD `4e7a17cd5d5723313f459753663d0d155f047e19` (2026-10-15); the installed CLI was built from a commit dated 2026-10-23, newer than the checkout (README.md "Version skew"). A separate `photocraft-pro-cli` exists in `~/bin/craft-cli`; not examined.

## Native file format

`.pcraft` [src: `book/src/formats/pcraft.md`]: ZIP archive **or directory bundle** with `manifest.json` (versioned document tree), `tiles/<blake3>.zst` and `blobs/<blake3>.zst` (content-addressed, zstd), `thumb.png`, `composite/preview.png`. Loader limits: manifest 256 MiB, blob 1 GiB, total 16 GiB, group nesting 100. Newer format versions fail explicitly.

## Readable / writable formats

- Read/write, per README [src]: PSD, PSB, layered TIFF, OpenRaster `.ora`, PNG, JPEG, TIFF, WebP, GIF, BMP, TGA, ICO, QOI, PNM, OpenEXR, Radiance HDR, FITS, native `.pcraft`.
- Read only [src]: Paint.NET PDN3, Krita `.kra`, SVG (opens as shape layers / places as vector Smart Object), camera raw (DNG, CR2, TIFF/EP via `photocraft-raw`), HEIF/HEIC (optional `photocraft-heif`).
- CLI `convert` flags confirm output options for jpg/webp/tiff/tga/dpx/dds/psd/exr [CLI]. The exact writable list was **not** enumerated by me; treat the README list as unverified for write support of ico/qoi/pnm/hdr/fits.
- **PDF input: not supported** (no PDF reader found; the only PDF commands are export). **PDF output** is raster: `file.export.artboardsToPdf` ("one raster page per board"). **SVG output: none** found.

## CLI surface [CLI]

Subcommands: `convert`, `info`, `run`, `batch`, `droplet`, `commands`, `mcp`, `serve`.
- `convert <in> <out> [--format ext] [--quality 1-100] [--in-place] [--tiff-layers] [--tiff-compression ..] [--tga-bits ..] [--dpx-bits ..] [--dds-compression ..] [--dds-mipmaps] [--jpeg-format ..]`; refuses out == in unless `--in-place`.
- `run (<file> | --new <json>) --cmd <id> [--params <json>] [--cmd ..] [--out <file>] [--format ext] ...`: opens or creates a document, runs commands in order, saves; prints each command's JSON result. Failure: `error: \`id\`: unknown command ...`, exit 1 (verified). `--new` takes e.g. `{"width":64,"height":64}`.
- `batch --actions <actions.json|set.atn> [--action name] --in <dir> --out <dir>`: applies a recorded action list (or a Photoshop `.atn` set) to every image in a folder. `droplet <file.pcdroplet> <files>`: runs a droplet.
- `serve [--port N] [--control-token ..]`: long-lived headless session speaking JSON lines (`engine.execute`, `doc.open/new/place/save/exportLayers/inspect/render/select/close`, `batch`, `jobs.list/cancel`, ...). This is the only product with a documented persistent stdio/TCP session protocol besides MCP (`docs/control-protocol.md`).
- `mcp [--bridge 127.0.0.1:port] [--control-token ..] [--automation-read-root ..] [--automation-write-root ..]`. Unlike the others the flags differ: read/write roots exist in this CLI's help (AGENTS.md of mcruft says there are none; the help I ran lists them, so that landmine note is stale or applies to `photocraft-pro-cli`).

## Command catalogue [CLI `commands --json`, counted]

935 commands. Groups: layer 221, filter 124, edit 79, image 66, type 66, file 58, select 35, view 31, paint 26, channel 22, path 21, actions 18, brush 17, layerComp 14. Key ids:
- File: `file.new {width,height,mode,depth,background,resolution,...}`, `file.saveACopy {path, quality, layers, overwrite, tiffLayers, ...}`, `file.openAs`, `file.placeEmbedded {path, scale, fit, smartObject, center}`, `file.placeLinked`, `file.export.quickExport`, `file.export.layersToFiles`, `file.export.artboardsToFiles`, `file.export.artboardsToPdf`, `layer.exportAs {layer, path, scale}`, `file.package`, `file.export.presets.*`.
- Open and save of the working document are MCP/serve methods (`doc_open`, `doc_save`), not registry commands.
- Type: `type.create`, `type.setStyle`, character/paragraph style commands (66 `type.*`).

## MCP surface [MCP]

`photocraft-cli mcp` (0.15.1), 25 tools: `command_list`, `command_run`, `command_batch`, `control_call`, `doc_new`, `doc_open`, `doc_close`, `doc_save`, `doc_export`, `doc_export_layers`, `doc_export_data_sets`, `doc_import_data_sets`, `doc_place`, `doc_select`, `doc_inspect`, `doc_render_preview`, `render_preview`, `jobs_list`, `jobs_cancel`, `session_list`, `ui_inspect`, `ui_menu_invoke`, `ui_pointer`, `ui_screenshot`, `ui_set`. Implemented in `photocraft-automation` with `rmcp` + tokio + schemars (a different stack from the hand-written JSON-RPC servers in the other four). `ui_*` need bridge mode. Paths are relative to granted read/write roots.

## Rust crates (25 in `crates/`)

| crate | role | bindable as library? | notable deps |
|---|---|---|---|
| doc, raster, geom, color, cms | document model, pixel buffers, geometry, colour, ICC | yes | serde |
| format | `.pcraft` bundle | yes | blake3, ruzstd, crc32fast |
| io | PSD/PSB + flat raster import/export | yes | links psd, codecs, raw, affinity, vector, text |
| psd | PSD/PSB reader/writer | yes | flate2 |
| codecs, heif, raw | flat codecs, HEIC, camera raw | yes | image, png, tiff, exr, heic-rs |
| compose, vector, paint, text, algo, ops | compositor, shape layers, brushes, type (parley), filters, ops | yes | parley, rustfft |
| affinity | Affinity reader | yes | - |
| engine | command registry and session | yes, but heavy | rayon, craft-print, plugins |
| gpu | optional wgpu compositor | no (GPU) | wgpu |
| plugins | wasmi filter plug-ins | no | wasmi |
| automation | MCP/bridge server | no | rmcp, tokio, cap-std |
| tablet, ui-egui, testkit | pen input, GUI, tests | no | egui |

No PyO3 in the repo.

## Operations relevant to mcruft

| operation | route |
|---|---|
| pages | no page list. Closest: artboards (`file.export.artboardsToFiles/ToPdf`) and layer comps (14 `layerComp.*`) |
| PDF embedded vs outlined fonts | not applicable: PDF is a raster per artboard |
| export PNG | `file.saveACopy path=x.png`, `convert`, `doc_export`, `quickExport` |
| export SVG | none |
| import PDF | none |
| place image | `file.placeEmbedded` / `file.placeLinked`, MCP `doc_place` |
| text edit | `type.create`, `type.setStyle`; type layers stay editable and round-trip through PSD [src] |

## Known gaps vs Photoshop [src: docs/gaps.md]

PSD fidelity beyond the test corpus, missing tools, workspaces shown only as parameter dialogs, type depth, scripting/Actions, Camera Raw depth, AI/generative features, plug-in compatibility, brush feel and a bug backlog. Re-saving PSD preserves render for 307/309 psd-tools files (self-reported).
