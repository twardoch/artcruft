---
this_file: docs/research/products/deckcraft.md
---

# DeckCraft

Evidence key: **[CLI]** = `deckcraft-cli` 0.10.0 help/run; **[MCP]** = live `tools/list`; **[src]** = repo docs/source; **[unverified]**.

## Purpose and reference product

Presentation app (Microsoft PowerPoint clone). Repo `storytold/deckcraft`, `MIT OR Apache-2.0`. Git HEAD `9859da39255c0262cd592bb57101d7f2fa961f72` (2026-10-14). Workspace version 0.7.0; installed CLI 0.10.0 (version skew, see README.md).

## Native file format

`.deckcraft` [src: `crates/format`]: ZIP containing a JSON manifest plus media; lossless for the DeckCraft model, forward compatible. `.slidecraft` is read as an alias [src: file-format-parity.md]. The model (`deckcraft-model`) has presentations, masters, layouts, slides, shapes, text, themes, transitions, animations. Default slide 960x540 pt.

## Readable / writable formats

- Read [CLI convert/run help + src]: `.deckcraft`, `.pptx`; `.potx`/`.ppsx` read as presentations; `.txt` outline and `.md` (headings = slides) through `slide.fromOutline`. Not read: `.ppt`, `.pptm`, `.odp`, PDF, SVG pictures.
- Write [CLI `convert`]: `.deckcraft`, `.pptx`, `.pdf`, `.txt`/`.md` (outline), `.png`/`.jpg` (first slide or `file.export` with `slide`/`all`), `.gif` (animated, one frame per slide). `.potx/.ppsx` are written with `.pptx` content type [src].
- PDF export [src: file-format-parity.md]: slides, notes pages, handouts (1-9 per page), selectable text layer with embedded font subsets, links, bookmarks; **slide artwork is rasterised** (gap 14). `file.export` params list no outline-text option (verified from command text).

## CLI surface [CLI]

Subcommands: `info`, `render`, `render-transition`, `convert IN OUT`, `run`, `commands`, `describe CMD`, `app`, `mcp`, `bench`, `links`, `--version`.
- `run [--in FILE | --sample] [--cmd ID[=JSON]]... [--save OUT] [--export OUT [--export-params JSON]] [--print]`: no `--in` starts a new deck with an empty title slide. Commands run in order; **if one fails, run stops and saves nothing** (verified: `deckcraft-cli: unknown command ...`, exit 1). `--print` shows each answer (`slide.new → {"id":260,"index":1}`). Slide indices 0-based; rect = `[x,y,w,h]` pt, y down; shape ids resolve on the current slide only.
- `--save` writes .deckcraft/.pptx/.pdf/.md; `--export` writes png/jpg/pdf/pptx/gif.

## Command catalogue [CLI `commands`, counted by regex, approx.]

About 321 commands. Groups: format 46, shape 33, table 21, file 19, slide 19, insert 18, text 16, arrange 15, design 14, smartArt 13, edit 12, picture 12, animation 11, review 11, media 9. Key ids:
- File: `file.new {theme,template,size}`, `file.open {path}`, `file.openBytes`, `file.save {path,format: deckcraft|pptx}`, `file.saveAs`, `file.saveBytes`, `file.export {path, format: png|jpeg|pptx|deckcraft|outline|pdf|gif, slide, all, slides, scale, layout: slides|notes|handouts, perPage, paper, dpi, ...}`, `file.render`, `file.info`.
- Slides (page ops): `slide.new {layout,title,...}`, `slide.duplicate`, `slide.delete {index|ids}`, `slide.move {from,to}`, `slide.go`, `slide.hide`, `slide.layout`, `slide.notes`, `slide.inspect`, `slide.fromOutline`, `slide.reuse` (import slides from another deck).
- Content: `insert.picture {path|data, rect}`, `insert.textBox {rect,text}`, `insert.table`, `insert.chart`, `shape.insert {preset,rect,text}`, `text.set {id,text}`, `text.get`, `text.find/replace`, `text.insert`.

## MCP surface [MCP]

`deckcraft-cli mcp` (0.10.0), 25 tools: `list_commands`, `run_command`, `batch`, `new_presentation`, `open_presentation`, `save_presentation`, `export`, `inspect_document`, `inspect_slide`, `render_slide`, `add_slide`, `go_to_slide`, `add_shape`, `add_text_box`, `set_text`, `insert_picture`, `insert_table`, `insert_chart`, `select`, `pointer`, `select_tool`, `key`, `type_text`, `screenshot`, `call_app`. Headless in-process by default; `--connect` attaches to a running app [unverified for deckcraft; flag shape from help of others]. Source: `crates/mcp` (hand-written JSON-RPC).

## Rust crates (24 in `crates/`)

| crate | role | bindable as library? | notable deps |
|---|---|---|---|
| model | presentation/slide/shape/text model | yes | serde, unicode-segmentation |
| format | `.deckcraft` zip+JSON, outline import/export | yes | zip, serde_json |
| pptx | OOXML PresentationML import/export | yes | quick-xml, zip |
| pdf | PDF export (slides, notes, handouts) | yes (needs craft-libs `craft-pdf`) | craft-pdf (krilla), kurbo |
| render | slide to pixels | yes | vello_cpu, skrifa |
| text, fonts, geom, color, anim, metafile | layout, font db, geometry, colour, animation timing, EMF/WMF | yes | harfrust, skrifa, kurbo |
| engine | session, undo, command registry, pointer tools | yes, but heavy | links `media` (video/audio decoders), i_overlay |
| media, av1, h264, hevc, vp9, opus, ogg, isobmff, matroska, bitstream | clean-room codecs and containers | no (not needed for doc work) | rayon, symphonia |
| mcp | MCP server | no | - |
| ui-egui | GUI | no | egui |

pydoccraft already links `deckcraft-model/pdf/pptx/render` from a fork at rev `16de1ca8...` (see vendors.md).

## Operations relevant to mcruft

| operation | route |
|---|---|
| add/remove/reorder slides | `slide.new/delete/move/duplicate`, 0-based |
| PDF, embedded fonts | `file.export format:pdf` (subsets embedded; art rasterised) |
| PDF, outlined fonts | not available (no switch found) |
| PNG | `file.export format:png`, `render`, `file.render` |
| SVG export | none |
| import PDF | not supported |
| place image | `insert.picture {path, rect}` (PNG/JPEG/GIF/BMP/TIFF/WebP; SVG not rendered [src]) |
| text frame edit | `insert.textBox`, `text.set {id,text}`, MCP `set_text` |
| single-page PDF | `file.export format:pdf slides:[i]` (param exists; not run by me) |

## Known gaps vs PowerPoint [src: docs/gaps.md]

PPTX corpus is only self-authored decks; round-trip drops some media options; SVG pictures do not render; no printing; only Regular/Bold/Italic font faces; PDF export rasterises slide art; English-only UI; no `.ppt/.pptm/.odp`. File-format dimension self-scored ~58% ready (estimate).
