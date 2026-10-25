---
this_file: DEPENDENCIES.md
---

# Dependencies

| Dependency | Purpose |
|---|---|
| pypdf | Inspect, extract and combine PDF pages |
| python-pptx | Inspect presentation slide dimensions/count |
| Pillow | Inspect image dimensions/DPI and render raster pages at the requested DPI |
| pypdfium2 (`pdf` or `libs` extra) | Render selected PDF pages to PNG; bundled PDFium, calls serialized by a module lock |
| resvg-py (`svg` or `libs` extra) | Render static SVG to PNG at the requested DPI; bundled Rust renderer, system fonts |
| psd-tools (`psd` or `libs` extra) | Inspect PSD canvas dimensions and resolution without a CLI |
| mcp (optional extra) | Official SDK stdio client |
| hatchling + hatch-vcs | Pure Python builds and repository-derived versions |
| pytest + ruff (dev group) | Offline tests, lint and formatting |
| maturin + PyO3 (optional native project) | Build abi3-py312 Rust extension |
| pdfcraft-cos + pdfcraft-organize | Native page count/extract/combine |

All PdfCraft crates and the five hayro/lopdf patches use release v0.13.0 commit
`53199fb4fa36f3c95b539add6218c57aeb2f823c` from `https://github.com/storytold/pdfcraft`.
No path dependencies reference vendor checkouts. The native extension is outside the uv
workspace. CLI binary wheels are separate optional distributions and perform no downloads.
Workspace exclusions for unpublished binary distributions are explained in WORK.md.
VectorCraft and PdfCraft declare their direct `pypdf` imports as package dependencies.
