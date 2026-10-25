---
this_file: README.md
---

# mcruft

One Python API for slide decks, PDFs, vector art, layouts and images. Behind it are the
ArtCraft apps, open-source clones of software with decades of cruft.

```python
import mcruft

doc = mcruft.new("Talk")
doc.add_file("deck.pptx")  # two slides -> two pages
doc.add_file("poster.svg")  # one more page
doc.save("Talk.mcruft", previews=True)

doc.export("talk.pdf", policy="editable")  # selectable text, fonts embedded
doc.export("talk-print.pdf", policy="fidelity")  # fonts outlined, looks the same everywhere
doc.export("talk.png", policy="fidelity", dpi=72)  # talk-0000.png, talk-0001.png, ...
doc.export("talk-images.pptx", policy="fidelity")  # one picture per slide
```

Every conversion asks you to choose: `editable` keeps the structure and may lose appearance;
`fidelity` keeps the appearance and may lose the structure. Each call returns a `Report` that
lists what was lost, for example `raster` when DeckCraft rasterises slide art, or `layout` when a
PDF is re-imported to outline its fonts. A route that cannot honour a policy raises
`UnsupportedRoute` instead of quietly doing the other thing.

## The `.mcruft` package

A `.mcruft` file is a folder:

- `manifest.json` lists the pages and the native files they point into, for example
  `deck.pptx#1` or `poster.svg#0`.
- `assets/` holds those native files, copied in once and never rewritten.
- `derived/` holds files that mcruft produced, each with its provenance recorded.
- `previews/` holds optional single-page PDFs, one per page, in the manner of old Keynote.

mcruft never translates your files into a format of its own. See [SPEC.md](SPEC.md) §3.

## Engines

| Package | Wraps | Does |
|---|---|---|
| `mcruft` | pypdf, python-pptx, Pillow | inspect pdf/pptx/svg/png; extract and combine PDF pages |
| `mcruft-vectorcraft` | `vectorcraft-cli` | svg/pdf/ai/vectorcraft conversion, PDF import as vectors, **outlining text** |
| `mcruft-deckcraft` | `deckcraft-cli` | pptx/deckcraft, slide export to PDF/PNG, decks built from images |
| `mcruft-photocraft` | `photocraft-cli` | png/jpg/psd/pcraft conversion |
| `mcruft-pdfcraft` | `pdfcraft-cli` | page rendering and extraction |
| `mcruft-pdfcraft` (`pdfcraft-native`) | optional `mcruft_pdfcraft_native` binding | native PDF extraction and combination |
| `mcruft-designcraft` | `designcraft-cli` | idml/designcraft to pdf, pptx and png |

The router picks an engine by capability, in the order verified, native, library, CLI, MCP.
`mcruft.engines()` shows what is installed. The tested routes are in [SPEC.md](SPEC.md) §5.
`mcruft[libs]` adds pypdfium2, resvg-py and psd-tools to the library engine, which the router prefers over CLIs.
Each CLI is found through `$MCRUFT_<PRODUCT>_CLI`, then a bundled `mcruft-<product>-bin` wheel,
then `PATH`. `engine.session()` opens the product's MCP server for interactive work
(`mcruft[mcp]`).

## Install

The packages are not on PyPI yet. From a clone:

```bash
uv sync --all-packages --all-extras
uv run python -c "import mcruft; print([(e.name, e.available) for e in mcruft.engines()])"
```

`mcruft[engines]` is the metapackage: it installs the core and all five engine packages.

The ArtCraft CLIs (macOS) come from the ArtCraft releases. To bundle one into its own wheel,
run `uv run python tools/bundle_cli.py <product>`. That writes a separate
`mcruft_<product>_bin-<version>-py3-none-macosx_11_0_arm64.whl` (29–51 MB) containing the
binary and a NOTICE, with nothing to download at run time. `native/mcruft_pdfcraft_native` is a proof PyO3 binding to pinned
PdfCraft crates, built with `maturin build`.

## Not yet

These are not in the MVP:

- Text editing (`frame.set_text`).
- Frame-level round trips.
- Video and audio operations. FilmCraft, EffectCraft and SoundCraft are in batch 2, along with
  WordCraft, FigCraft, CADCraft, GridCraft and LightCraft.
- Linux and Windows binary wheels.

## Development

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest -q          # real-CLI tests skip when a CLI is missing
```

- How agents work on this repo: [docs/workflow.md](docs/workflow.md).
- Research behind the design: [docs/research/](docs/research/).
- Rules for agents: [AGENTS.md](AGENTS.md).

Licence: Apache-2.0. The ArtCraft apps are MIT OR Apache-2.0 and belong to their authors.
mcruft names them only to say what it drives.
