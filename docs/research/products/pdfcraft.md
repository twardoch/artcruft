---
this_file: docs/research/products/pdfcraft.md
---

# PdfCraft

Evidence key: **[CLI]** = `pdfcraft-cli` 0.13.0 help and `tools`; **[MCP]** = live `tools/list`; **[src]**; **[unverified]**.

## Purpose and reference product

PDF viewer/editor (Adobe Acrobat Pro clone; parity target Acrobat DC 26.002). Repo `storytold/pdfcraft`, `MIT OR Apache-2.0`. Git HEAD `dc41044ba78f6cef2ff4bdb14d19272f54ad6aea` (2026-10-15). Workspace 0.8.0 vs installed CLI 0.13.0 (version skew, README.md). The artcraft-in-a-box web bundle ships this repo as "PrintCraft" v0.2.1, i.e. the product has been renamed or double-branded; mcruft must not assume the name.

## Native file format

PDF itself (no separate container). `pdfcraft-cos` is a lazy, tolerant object layer with copy-on-write edits and incremental or full save; `pdfcraft-model` gives typed page views. Passwords supported (`--password`); encryption RC4/AES rev 2-6.

## Readable / writable formats

- Read: PDF (incl. encrypted, XFA forms). `doc_create` / `doc_create_multiple` turn PNG, JPEG, JPEG 2000, TIFF, GIF, BMP and `.txt` into PDF [MCP descriptions]. Office import is absent [src: gaps.md gap 8].
- Write: PDF; PDF/A-2b and 3b conversion (`pdfa_convert`); pages as PNG/JPEG/TIFF (`doc_export_images`, `page_render`; CLI `render` also .pam); text (`doc_export_text`); Word `.docx`, PowerPoint `.pptx` (one slide per page), HTML, RTF via `doc_export_office` ("Office export weak" per gaps.md); XFDF/FDF/XML/CSV form and comment data.
- **No SVG export.** No font-outline switch: this is an editor of existing PDFs, so fonts are whatever the file embeds; new text goes through `text_font_import` (validates embeddable licences).

## CLI surface [CLI]

Subcommands: `info`, `render`, `text`, `edit`, `combine`, `extract`, `split`, `check`, `audit`, `batch`, `tools`, `run`, `mcp`, `ui`.
- `edit <in> --out <out> [--rotate 1,3:90] [--delete 2,4] [--move 5:1] [--insert-blank 1] [--title ..] [--author ..] [--full]`: options run in order; page numbers 1-based and refer to the document after earlier options.
- `extract <in> --pages 1,3,5-8 --out out.pdf`, `split <in> (--every N | --before 3,7) [--out-dir]`, `combine a.pdf b.pdf --out c.pdf`.
- `batch <files|dirs> --steps convert,ocr,optimize --out-dir DIR [--recursive] [--ppi] [--quality] [--dpi] [--language]`.
- `run <tool> [key=value ...] [--root DIR] [--out image.png]` or `run --script steps.json [--report]` where steps are `[{"tool":"doc_open","args":{...}}, ...]`. Tool names are the MCP tool names. Errors: `pdfcraft-cli: <tool>: unknown argument "blank" (expected: dpi, from, height, ...)`, exit 1 (verified). Tools are stateless per process unless a script keeps the doc id; I did not test multi-step state.
- `tools` prints all tools with JSON Schemas (175 entries; the same data is `tools/list`).
- `mcp [--root DIR] [--compact] [--automation-read-root ..] [--automation-write-root ..]`: `--compact` lists a core set plus `tool_search`/`tool_call`.

## Command / tool catalogue [CLI `tools`, MCP]

175 tools. Document: `doc_open {path,password}`, `doc_create {pages,width,height | images | text}`, `doc_info`, `doc_save`, `doc_close`, `doc_set_info`, `doc_combine`, `doc_split`, `doc_batch`, `doc_inspect`. Pages: `page_rotate`, `page_delete`, `page_move`, `page_reverse`, `page_insert_blank`, `page_insert_file`, `page_extract`, `page_duplicate`, `page_replace`, `page_set_box`, `page_render`, `page_add_text`, `page_add_image`, `page_images`, `image_edit`, `image_save`. Content: `content_list/update/delete`, `text_extract`, `text_find`, `text_edit.*` [exact id unverified], `text_fonts`, `text_font_import`. Plus bookmarks, forms (AcroForm/XFA), annotations, redaction, signatures, accessibility (check, tagging), OCR, optimizer, compare, measure, print, JavaScript, headers/footers/watermarks. Many tools map to a `command` id (`page.rotate`, `file.save`, `page.insert`, ...) usable by `command_run`.

## MCP surface [MCP]

`pdfcraft-cli mcp` (0.13.0, 175 tools listed non-compact). Open documents are MCP resources: `pdfcraft://doc/{doc}/info`, `/text`, `/page/{page}/text`, `/page/{page}/image`. Edits are in memory and undoable (`edit_undo`) until `doc_save`. Page numbers 1-based. Source: `pdfcraft-automation` (headless tool set + MCP).

## Rust crates (33 in `crates/`)

| crate | role | bindable as library? | notable deps |
|---|---|---|---|
| cos, model, content, filters, crypt | object layer, page tree, content streams, stream filters, encryption | yes | flate2, aes |
| organize, create, edit | page ops, create from images/text, headers/footers/watermarks | yes | - |
| render | page to pixels | yes (renderer is borrowed: `hayro`) | hayro, lopdf (patched copies in `vendor/`) |
| export | PDF to HTML/docx/RTF | yes | flate2 |
| fonts, forms, annot, xfdf, xfa, redact, optimize, preflight, measure, compare, a11y, audit, print | features | yes (pick per need) | print needs craft-print |
| ocr | text recognition | yes but needs model files | rten, ocrs |
| js, sign | Acrobat JS (boa), digital signatures | yes but heavy and risky | boa_engine, rsa, p256 |
| engine | facade over everything | yes, very heavy | image, icu |
| automation | tool set + MCP | no | tempfile |
| platform, ui-egui, oracle, testkit | OS services, GUI, test | no | egui |

`Cargo.toml` has `exclude = ["vendor"]`: patched `hayro`/`lopdf` live in `vendor/` and a consumer must re-declare them in its own `[patch.crates-io]` (pydoccraft does).

## Operations relevant to mcruft

| operation | route |
|---|---|
| page add/remove/reorder | `page_insert_blank`, `page_insert_file`, `page_delete`, `page_move`, `page_duplicate`, `page_reverse`; CLI `edit` |
| embedded vs outlined fonts | n/a (existing PDF); no outline switch |
| export PNG / SVG | PNG/JPEG/TIFF yes (`page_render`, `doc_export_images`); SVG none |
| import PDF | native; merge via `doc_combine` / `page_insert_file` |
| import images | `doc_create images:[...]`, `page_add_image {rect}` |
| text edit | `page_add_text`, `content_update`; editing existing text is flagged fragile (gap 3) |
| single-page PDF | `page_extract` / CLI `extract --pages N` |

## Known gaps vs Acrobat Pro [src: docs/gaps.md]

Renderer borrowed and fidelity unmeasured; editing existing text fragile on real files; OCR only unaccented Latin; Office export weak, Office import absent; PDF/A partial, no PDF/X or PDF/UA; signatures lack PKCS#11, timestamp servers, revocation; accessibility checker without full tagging tools.
