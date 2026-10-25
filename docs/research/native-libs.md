---
this_file: docs/research/native-libs.md
---

# Native-format libraries for mcruft

Research snapshot: **2026-10-25**. Third-party libraries only; these are dependency recommendations, not implemented or tested conversions. DOCX/XLSX research does not expand the batch-1 product scope.

Release cells link to live PyPI JSON (version and earliest upload date of that version's files) or crates.io JSON (latest non-yanked stable release). Stars are GitHub repository counts queried on this date; `~` preserves GitHub's rounded display. Repository links supply upstream licensing, capabilities and maintenance evidence. Binding and engine releases are different products and may have different versions.

Wheel notation: **B M/L/W** = binary wheels listed for macOS arm64 / Linux x86-64 / Windows x86-64; this does not promise every Python ABI or minimum OS. **U** = universal pure-Python wheel usable on those platforms, not a binary wheel. **N/A** = Rust crate without a verified distributed Python wheel. Dependencies installed as separate wheels are not bundled inside the parent wheel. “Core included” confirms the compiled extension, not a complete dynamic-linkage audit.

Native archive check: downloaded nine macOS wheels into memory, without installation. Confirmed `libpdfium.dylib` in pypdfium2; qpdf and libjpeg dylibs in pikepdf; Rust extensions in pdf-oxide, resvg-py and python-calamine; the RLE extension in psd-tools; bundled codecs, FreeType and HarfBuzz in Pillow; and extensions in uharfbuzz and lxml. Linux/Windows archive contents and full transitive linkage on **all** platforms remain **unverified**. Standard OS runtimes are excluded from “native dependency”.

## PDF

| Name | Lang/binding | License | Latest release (date) | Stars | Wheels bundle natives? | Read | Write | Notes |
|---|---|---|---|---:|---|---|---|---|
| [pdf-oxide](https://github.com/yfedoseev/pdf_oxide) | Rust / PyO3, maturin | MIT OR Apache-2.0 | [0.3.78 (2026-09-08)](https://pypi.org/pypi/pdf-oxide/json) | 1,091 | B M/L/W; core included; upstream says no system deps | Yes | Yes | Extraction, creation, editing and rendering; newer alternative, not proven feature-equivalent to MuPDF. OCR is optional and must be excluded from an offline base. |
| [oxidize-pdf](https://github.com/bzsanti/oxidize-python) | Rust / PyO3 | MIT binding; verify pinned core notices | [0.22.0 (2026-10-11)](https://pypi.org/pypi/oxidize-pdf/json) | 6 (binding) | B M/L/W; core included per upstream; native closure unverified | Yes | Yes | Separate project from PDF Oxide; upstream pins core 5.4.2. Generate, parse, split, merge; optional MCP excluded. |
| [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) | Python ctypes / C++ PDFium | Apache-2.0 OR BSD-3-Clause wrapper; PDFium BSD-style + dependency notices | [5.14.0 (2026-10-04)](https://pypi.org/pypi/pypdfium2/json) | 841 | B M/L/W; PDFium bundled | Yes; render | Limited creation/edit/save | Permissive renderer; latest arm64 macOS wheel requires macOS 13. Source installation can fetch build binaries; use wheels. |
| [pikepdf](https://github.com/pikepdf/pikepdf) | C++ qpdf / nanobind | **MPL-2.0**, file-level copyleft; qpdf Apache-2.0 | [10.17.0 (2026-10-11)](https://pypi.org/pypi/pikepdf/json) | 2,816 | B M/L/W; qpdf bundled | Yes | Yes | Strong structural repair/page operations; no page renderer. Latest macOS arm64 wheel tag requires **macOS 15**, despite older installation prose. |
| [pypdf](https://github.com/py-pdf/pypdf) | Pure Python | BSD-3-Clause | [6.21.2 (2026-10-21)](https://pypi.org/pypi/pypdf/json) | 10,271 | U; no core natives; AES extra separate | Yes | Yes | Merge/split, objects, metadata, extraction; no rendering/layout engine. |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | Python / C MuPDF | **AGPL-3.0 or commercial** | [2.0 (2026-10-19)](https://pypi.org/pypi/PyMuPDF/json) | 10,988 | B M/L/W; MuPDF included by upstream distribution; full closure unverified | Yes; render | Yes | Exclude from permissive default; pypdfium2 renders and PDF Oxide/pypdf manipulate without AGPL. |
| [lopdf](https://github.com/J-F-Liu/lopdf) | Rust; maintained Python binding unverified | MIT | [0.46.0 (2026-10-21)](https://crates.io/api/v1/crates/lopdf) | 2,286 | N/A; Python wheels unverified | Yes | Yes | Low-level PDF objects/manipulation, not a renderer; custom binding work. |
| [pdf-rs (`pdf`)](https://github.com/pdf-rs/pdf) | Rust; Python binding unverified | MIT | [0.10.0 (2026-03-02)](https://crates.io/api/v1/crates/pdf) | 1,718 | N/A; Python wheels unverified | Yes | Yes | Upstream explicitly supports read/alter/write; not a ready Python document engine. |
| [borb](https://github.com/borb-pdf/borb) | Python | **AGPL-3.0-or-later** | [3.0.9 (2026-08-03)](https://pypi.org/pypi/borb/json) | 3,572 | U; dependencies separate | Yes | Yes | Exclude from permissive default; ReportLab supplies permissive PDF generation. |
| [ReportLab](https://www.reportlab.com/) | Python; optional accelerators | BSD | [5.1.0 (2026-10-22)](https://pypi.org/pypi/reportlab/json) | N/A; canonical GitHub count unverified | U; Pillow separate; optional acceleration/render backends separate | No general PDF reader | Yes | Established page authoring and font embedding; PDF generation does not require Cairo. |
| [fpdf2](https://github.com/py-pdf/fpdf2) | Python | **LGPL-3.0-only** | [2.8.9 (2026-09-29)](https://pypi.org/pypi/fpdf2/json) | 1,552 | U; Pillow/fontTools separate | No general PDF reader | Yes | Useful authoring/font embedding, but less permissive than ReportLab. |
| [pdfplumber](https://github.com/jsvine/pdfplumber) | Python / pdfminer.six | MIT | [0.11.10 (2026-06-15)](https://pypi.org/pypi/pdfplumber/json) | 10,851 | U; renderer/other native deps separate | Yes | No PDF authoring | Detailed characters, geometry, tables; extraction adjunct, not an editor. |

Sources for bundling and limits: [pikepdf installation](https://pikepdf.readthedocs.io/en/stable/installation.html), [pypdfium2 distribution/licensing](https://pypi.org/project/pypdfium2/), [PDF Oxide Python API](https://pdf.oxide.fyi/rust/docs/reference/python-api), [pdf-rs read/alter/write](https://raw.githubusercontent.com/pdf-rs/pdf/master/README.md). Newer Rust packages have recent activity but need corpus acceptance testing; upstream benchmark claims are not independent evidence.

## SVG

| Name | Lang/binding | License | Latest release (date) | Stars | Wheels bundle natives? | Read | Write | Notes |
|---|---|---|---|---:|---|---|---|---|
| [resvg-py](https://github.com/baseplate-admin/resvg-py) (`resvg_py`) | Rust / PyO3 | MIT binding; resvg MIT OR Apache-2.0 | [0.5.0 (2026-08-24)](https://pypi.org/pypi/resvg-py/json) | 28 | B M/L/W; Rust core included; no Cairo | SVG | PNG, not editable SVG | Small, active wrapper; fonts must be supplied for reproducibility. |
| [resvg](https://github.com/briceyan/resvg-py) (different PyPI package) | Rust / PyO3 | MIT binding; upstream dual license | [0.2.0 (2026-04-14)](https://pypi.org/pypi/resvg/json) | 14 | B M/L/W; core included per build; closure unverified | SVG / exposed usvg tree | PNG | Alternative lower-level interface; not the `resvg-py` distribution above. |
| [usvg / resvg crates](https://github.com/linebender/resvg) | Rust; wrappers above | MIT OR Apache-2.0 | [usvg 0.49.0](https://crates.io/api/v1/crates/usvg), [resvg 0.49.0](https://crates.io/api/v1/crates/resvg) (2026-10-24) | ~4.2k shared | N/A directly; Rust implementation needs no Cairo | SVG normalization | usvg: normalized SVG; resvg: pixels | Static SVG, no browser scripting/animation; Python wrappers can embed older versions. |
| [CairoSVG](https://github.com/Kozea/CairoSVG) | Python / cairocffi / C Cairo | **LGPL-3.0-or-later** | [2.9.1 (2026-09-07)](https://pypi.org/pypi/cairosvg/json) | 956 | U; **does not bundle Cairo** | SVG | PDF/PS/PNG/SVG | System Cairo dependency disqualifies unchanged wheels from fully bundled default. |
| [svgelements](https://github.com/meerk40t/svgelements) | Pure Python | MIT | [1.9.6 (2023-08-17)](https://pypi.org/pypi/svgelements/json) | 171 | U; no mandatory native deps | Geometry | Basic SVG | Editable geometry adjunct; incomplete CSS and styling. Last repo push 2024-10-17: maintenance risk. |
| [svglib](https://github.com/deeplook/svglib) | Python / ReportLab, lxml | **LGPL-3.0-or-later** | [2.3.2 (2026-10-23)](https://pypi.org/pypi/svglib/json) | 371 | U; lxml/Pillow separate; bitmap backend can need Cairo | SVG | PDF via ReportLab; bitmap via backend | Active; masks/foreignObject unsupported; PDF route itself needs no Cairo. |

Evidence: [resvg no system libraries/static SVG](https://raw.githubusercontent.com/linebender/resvg/main/README.md), [wrapper build](https://raw.githubusercontent.com/baseplate-admin/resvg-py/master/Cargo.toml), [alternative wrapper build](https://raw.githubusercontent.com/briceyan/resvg-py/main/Cargo.toml), [CairoSVG installation](https://cairosvg.org/documentation/), [font supply](https://resvg-py.readthedocs.io/en/latest/fonts.html). Font files are not supplied by resvg wheels.

## PSD

| Name | Lang/binding | License | Latest release (date) | Stars | Wheels bundle natives? | Read | Write | Notes |
|---|---|---|---|---:|---|---|---|---|
| [psd-tools](https://github.com/psd-tools/psd-tools) | Python + compiled RLE accelerator | MIT | [1.26.0 (2026-10-21)](https://pypi.org/pypi/psd-tools/json) | 1,483 | B M/L/W; accelerator included; NumPy/Pillow separate | PSD/PSB, layers | Limited PSD/PSB edits | Active. Pixel/group editing and low-level saving; no text editing, font rendering or general smart-object editing. |
| [pytoshop](https://github.com/mdboom/pytoshop) | Python + Cython | BSD | [1.2.1 (2018-11-30)](https://pypi.org/pypi/pytoshop/json) | 128 | **No wheels** for latest release; source build | PSD/PSB | PSD/PSB | Last repo push 2022-09-07; unsuitable default despite useful writer. |
| [Rust `psd`](https://github.com/chinedufn/psd) | Rust; maintained Python binding unverified | MIT OR Apache-2.0 | [0.3.5 (2024-01-04)](https://crates.io/api/v1/crates/psd) | 283 | N/A; Python wheels unverified | Pixel layers/groups | No documented writer | Last repo push 2025-01-30; narrower parser, not a Photoshop editing engine. |

The [psd-tools capability list](https://psd-tools.readthedocs.io/en/latest/) distinguishes low-level read/write from unsupported high-level editing. Its `composite` extra adds aggdraw/scipy; wheel coverage for that entire extra is **unverified**. [Rust API](https://docs.rs/psd/latest/psd/) supplies parsing/layer structures, not a verified writer.

## PPTX

| Name | Lang/binding | License | Latest release (date) | Stars | Wheels bundle natives? | Read | Write | Notes |
|---|---|---|---|---:|---|---|---|---|
| [python-pptx](https://github.com/scanny/python-pptx) | Python / lxml, Pillow | MIT | [1.0.2 (2024-08-07)](https://pypi.org/pypi/python-pptx/json) | 3,565 | U; native deps have separate wheels | Yes | Yes | Established API; repo last pushed 2024-08-07. No slide renderer; incomplete Office feature editing. |
| [python-pptx-rs](https://github.com/wakita181009/python-pptx-rs) | Rust / PyO3, maturin | MIT | [0.0.1 (2026-07-05)](https://pypi.org/pypi/python-pptx-rs/json) | 0 | B M/L/W; core included per build; closure unverified | Yes | Yes, subset | Upstream documents 75 compatibility scenarios and remaining unimplemented APIs. Early candidate, not established drop-in parity. |
| [Rust `pptx`](https://github.com/hidemi-ito/rust-pptx) | Rust; Python binding unverified | MIT | [0.1.0 (2026-02-25)](https://crates.io/api/v1/crates/pptx) | 6 | N/A; Python wheels unverified | Yes | Yes | [API/readme](https://docs.rs/crate/pptx/latest/source/README.md) documents read/modify/save; adoption and fidelity need validation. |
| [ppt-rs](https://github.com/yingkitw/ppt-rs) | Rust; Python binding unverified | Apache-2.0 | [0.2.37 (2026-10-24)](https://crates.io/api/v1/crates/ppt-rs) | 50 | N/A; Python wheels unverified | Yes, upstream claim | Yes | Active; optional native PDF export differs from LibreOffice route. Not verified as PowerPoint-equivalent. |

## DOCX

| Name | Lang/binding | License | Latest release (date) | Stars | Wheels bundle natives? | Read | Write | Notes |
|---|---|---|---|---:|---|---|---|---|
| [python-docx](https://github.com/python-openxml/python-docx) | Python / lxml | MIT | [1.2.0 (2025-06-16)](https://pypi.org/pypi/python-docx/json) | 5,749 | U; lxml separate | Yes | Yes | Repo active into 2026; no Word pagination or PDF rendering. |
| [docx-rs](https://github.com/bokuweb/docx-rs) | Rust; Rust/WASM documented, Python binding unverified | MIT | [0.4.22 (2026-07-21)](https://crates.io/api/v1/crates/docx-rs) | 560 | N/A; Python wheels unverified | Yes, subset | Yes | Current upstream supports parsing and generation, not just writing; custom PyO3 binding needed for adoption. |
| [mammoth](https://github.com/mwilliamson/python-mammoth) | Pure Python | BSD-2-Clause | [1.13.0 (2026-09-26)](https://pypi.org/pypi/mammoth/json) | 1,120 | U; no native core | DOCX | HTML, not DOCX authoring | Semantic extraction; deliberately loses page/layout fidelity. Markdown output is deprecated. |

python-docx/python-pptx are Python implementations, but **not dependency-free pure-Python installations**. [lxml installation](https://lxml.de/installation.html) describes static binary distributions with libxml2/libxslt; source builds require native development libraries. Resolve and bundle dependency wheels explicitly.

## XLSX

| Name | Lang/binding | License | Latest release (date) | Stars | Wheels bundle natives? | Read | Write | Notes |
|---|---|---|---|---:|---|---|---|---|
| [calamine](https://github.com/tafia/calamine) | Rust; bindings below | MIT | [0.37.0 (2026-10-18)](https://crates.io/api/v1/crates/calamine) | ~2.5k | N/A directly | XLSX/XLS/XLSB/ODS | No | Reader, not workbook editor or formula evaluator. |
| [python-calamine](https://github.com/dimastbk/python-calamine) | Rust / PyO3, maturin | MIT | [0.9.0 (2026-10-16)](https://pypi.org/pypi/python-calamine/json) | 507 | B M/L/W; Rust core included | Yes | No | Active, simple value-oriented reader; not full style/layout preservation. |
| [fastexcel](https://github.com/ToucanToco/fastexcel) | Rust Calamine + Arrow / PyO3 | MIT | [0.21.0 (2026-08-19)](https://pypi.org/pypi/fastexcel/json) | 255 | B M/L/W; core included per build; closure unverified | Yes | No | Arrow-oriented; PyArrow **optional** through PyCapsule interface, not mandatory in base. |
| [rust_xlsxwriter](https://github.com/jmcnamara/rust_xlsxwriter) | Rust; third-party bindings below | MIT OR Apache-2.0 | [0.101.0 (2026-10-20)](https://crates.io/api/v1/crates/rust_xlsxwriter) | 595 | N/A directly | No | New XLSX | Active upstream. Python XlsxWriter is a separate implementation, **not its binding**. |
| [rustpy-xlsxwriter](https://github.com/rahmadafandi/rustpy-xlsxwriter) | Rust / PyO3 | MIT | [0.8.0 (2026-10-19)](https://pypi.org/pypi/rustpy-xlsxwriter/json) | 33 | B M/L/W; native closure unverified | No | New XLSX/CSV | Real distributed Rust writer binding; young ecosystem, API differs from XlsxWriter. |
| [rvgsrust-xlsxwriter](https://github.com/Godse4ever/rvgsrust-xlsxwriter) | Rust / PyO3, maturin | MIT | [0.3.5 (2026-09-16)](https://pypi.org/pypi/rvgsrust-xlsxwriter/json) | 3 | B M/L/W; native closure unverified | No | New XLSX | Another real rust_xlsxwriter binding; current build enables zlib; do not infer dependency closure from Rust alone. |
| [XlsxWriter](https://github.com/jmcnamara/XlsxWriter) | Pure Python | BSD-2-Clause | [3.3.0 (2026-10-22)](https://pypi.org/pypi/xlsxwriter/json) | 3,986 | U; no native core | No | New XLSX | Mature chart/formatting writer, cannot modify existing workbooks. |
| [openpyxl](https://foss.heptapod.net/openpyxl/openpyxl) | Pure Python; optional lxml/Pillow | MIT | [3.1.5 (2024-06-28)](https://pypi.org/pypi/openpyxl/json) | N/A; upstream on Heptapod | U; no required native core | Yes | Yes | Needed for workbook edits; older release, cannot preserve all Excel objects or calculate formulas. |

Evidence: [rust_xlsxwriter scope](https://rustxlsxwriter.github.io/), [third-party writer's build](https://raw.githubusercontent.com/Godse4ever/rvgsrust-xlsxwriter/main/Cargo.toml), [openpyxl editing and preservation limits](https://openpyxl.readthedocs.io/en/stable/tutorial.html). Rust writer bindings exist; the choice of Python XlsxWriter below reflects API maturity and packaging certainty, not absence of Rust bindings.

## Fonts

| Name | Lang/binding | License | Latest release (date) | Stars | Wheels bundle natives? | Read | Write | Notes |
|---|---|---|---|---:|---|---|---|---|
| [fontTools](https://github.com/fonttools/fonttools) | Python; optional compiled accelerators | MIT | [4.67.0 (2026-10-14)](https://pypi.org/pypi/fonttools/json) | 5,299 | U **and** B M/L/W; core needs no external libs | TTF/OTF/etc. | Fonts/subsets/outlines | Active. Pens expose glyph paths; no complete PDF font-outlining operation. |
| [skrifa / Fontations](https://github.com/googlefonts/fontations) | Rust; production Python binding unverified | MIT OR Apache-2.0 | [skrifa 0.49.0 (2026-10-21)](https://crates.io/api/v1/crates/skrifa) | 848 shared | N/A; Python wheels unverified | Font metadata/outlines | Not skrifa; separate write-fonts crate | Active Rust foundation; not a ready Python substitute for fontTools. |
| [uharfbuzz](https://github.com/harfbuzz/uharfbuzz) | Cython / C++ HarfBuzz | Apache-2.0 binding; HarfBuzz MIT-style | [0.57.0 (2026-10-23)](https://pypi.org/pypi/uharfbuzz/json) | 113 | B M/L/W; incorporates HarfBuzz sources | Font input, shaping | Glyph IDs/positions, not font/PDF authoring | Complement for shaping before outline emission; no system HarfBuzz needed by default. |

Evidence: [fontTools subsetter](https://fonttools.readthedocs.io/en/latest/subset/index.html), [SVGPathPen](https://fonttools.readthedocs.io/en/latest/pens/svgPathPen.html), [skrifa capability list](https://github.com/googlefonts/fontations/blob/main/skrifa/README.md). FontTools can produce subsets and paths; embedding them correctly is the PDF writer's responsibility.

## Raster

| Name | Lang/binding | License | Latest release (date) | Stars | Wheels bundle natives? | Read | Write | Notes |
|---|---|---|---|---:|---|---|---|---|
| [Pillow](https://github.com/python-pillow/Pillow) | Python / C codecs | MIT-CMU; bundled-library notices apply | [13.0.0 (2026-10-16)](https://pypi.org/pypi/Pillow/json) | 13,926 | B M/L/W; codecs bundled, exact feature set varies | Many rasters; limited PSD | PNG/JPEG/TIFF/etc. | General image backend, not layered PSD writer or PDF/SVG renderer. |
| pypdfium2 render | See PDF | See PDF | 5.14.0 (2026-10-04) | 841 | B M/L/W; PDFium bundled | PDF pages | Bitmaps/Pillow images | PDF visual-fidelity route; retains pixels, loses editable content. |
| resvg-py render | See SVG | See SVG | 0.5.0 (2026-08-24) | 28 | B M/L/W; Rust core included | Static SVG | PNG bytes | SVG visual-fidelity route, not SVG authoring. |

[Pillow binary installation](https://pillow.readthedocs.io/en/stable/installation/basic-installation.html) documents included image libraries. PDFium calls must be serialized or placed in separate processes: its [Python API documentation](https://pypdfium2.readthedocs.io/en/stable/python_api.html) prohibits simultaneous calls across threads, even for different documents.

## MVP selection

| Format | Primary library | Fallback | Rationale |
|---|---|---|---|
| PDF | pdf-oxide + pypdfium2 rendering | pypdf + ReportLab authoring | Rust/PyO3 operations plus permissive bundled renderer; mature Python manipulation/creation alternatives. |
| SVG | resvg-py rendering + svgelements geometry | resvg Python binding for rendering | Rust renderer without Cairo; basic editable geometry remains separate and limited. |
| PSD | psd-tools | Pillow composite-image read only | Best verified Python layer access and limited saving; no equivalent layered-writer fallback. |
| PPTX | python-pptx | python-pptx-rs, experimental subset | Established editing API; Rust wheels exist but compatibility is incomplete. |
| DOCX | python-docx | mammoth for semantic extraction only | Established editing API; extraction fallback deliberately discards pagination/layout. |
| XLSX | python-calamine reading + XlsxWriter creation | openpyxl for read/edit/save | Prefer Rust reader; mature permissive writer; existing-workbook edits need a separate engine. |
| Fonts | fontTools + uharfbuzz | fontTools alone for already positioned glyphs | Bundled shaping plus font subsetting/outlines; existing PDF text requires its original glyph positions. |
| Raster | Pillow | pypdfium2 / resvg-py for document rasterization only | Bundled raster codecs; source-specific renderers supplement rather than replace image editing. |

### Explicit default rejections / deferrals

- **PyMuPDF and borb:** AGPL risk; permissive alternatives exist above. A commercial MuPDF license is a separate decision.
- **CairoSVG:** system Cairo plus LGPL; use resvg for rendering. **svglib:** LGPL and incomplete SVG; its PDF path avoids Cairo, but its bitmap path may introduce it. **fpdf2:** LGPL, prefer BSD ReportLab for default generation. LGPL is not AGPL, but is still non-permissive.
- **pikepdf:** MPL is file-level copyleft, not AGPL; defer as optional repair backend when pypdf/PDF Oxide cannot meet requirements. Its current macOS 15 wheel minimum also narrows deployment.
- **pytoshop:** 2018 release, 2022 last repository push, no latest-release wheels. **Rust psd:** old release, no documented writer or verified Python distribution.
- **lopdf, pdf-rs, docx-rs, direct skrifa/PPTX crates:** useful Rust building blocks, but maintained Python binding/wheel availability is unverified; do not create custom bindings for the MVP solely to use Rust. Use usvg through the existing resvg wrappers when their exposed API suffices.
- **python-pptx-rs, rustpy-xlsxwriter, rvgsrust-xlsxwriter:** real Rust/Python distributions, deferred from default editing/writing due to early API/adoption or unverified native closure. They merit focused follow-up, not an assertion that Rust bindings do not exist.

## Risks and gaps

- **PDF text outlining is not solved by choosing a font library.** FontTools pens need glyph IDs, original advances/offsets, transforms, clipping and color; an existing PDF also needs font-resource/CMap interpretation and content-stream rewriting. Shaping Unicode again can change the original glyph sequence. Missing/subset fonts, Type 3 glyph programs and color fonts need explicit handling. No tested general outlining route is established here.
- **Font embedding:** subset/instance fonts as needed, preserve encodings/ToUnicode and resource references, and respect the font's embedding/subsetting permissions. Bundled engines do not imply bundled font files. Supply licensed font assets rather than relying on host substitution.
- **Editable conversion:** preserve native files and supported objects; report unsupported charts, effects, media, text and layout. **Visual-fidelity conversion:** render a page/slide to pixels when necessary and retain the native source; explicitly report lost editability/searchability. Rasterization cannot be described as a lossless editable round trip.
- **PSD:** no verified ready-to-use Rust/Python layered writer matching psd-tools; psd-tools itself cannot recreate arbitrary Photoshop text, smart objects or effects. Cached composites can differ from recomposition.
- **Office pagination:** python-pptx, python-docx, Calamine, openpyxl and XlsxWriter are not Office renderers. No faithful PPTX/DOCX/XLSX-to-PDF route has been verified here. XLSX data readers drop presentation details; writers do not evaluate formulas.
- **Wheel closure:** upstream wheels are inputs, not proof that a fully bundled `mcruft_<product>` wheel exists. Vendor required native libraries and Python dependencies during build, preserve notices and verify imports/rendering without network access. Reject accidental source-build fallbacks; disable OCR/model-download features unless assets are bundled.
- **Maintenance:** python-pptx and openpyxl have old releases; svgelements is older still. Recent commits and stars indicate activity/adoption, not correctness. New Rust alternatives need representative document tests before promotion.
- **Unverified facts register:** complete Linux/Windows native contents and all-platform dynamic linkage; psd-tools composite-extra wheel closure; canonical ReportLab GitHub star count; maintained Python bindings/wheels for lopdf, pdf-rs, Rust psd, docx-rs, direct skrifa, pptx and ppt-rs; oxidize-pdf's full pinned-core dependency license closure; broad reference-editor fidelity, PDF outlining and round-trip preservation. A missing binding found in research is not proof that none exists.
