---
this_file: docs/research/wheels-and-probe-2.md
---

# Wheel sizes and second probe

## Bundled-CLI wheel feasibility (measured 2026-10-25)

All five CLIs are macOS universal binaries (x86_64 + arm64), `minos 11.0`, linking only system
frameworks.

| CLI | Version | Universal raw | Universal zip -9 |
|---|---|---|---|
| vectorcraft-cli | 0.16.0 | 206.5 MB | 109.7 MB |
| deckcraft-cli | 0.10.0 | 148.2 MB | 72.4 MB |
| photocraft-cli | 0.15.1 | 143.7 MB | 70.7 MB |
| pdfcraft-cli | 0.13.0 | 127.5 MB | 62.4 MB |
| designcraft-cli | 0.12.0 | 150.9 MB | 71.0 MB |

`lipo -thin arm64` on vectorcraft-cli: 100.0 MB raw, 53.6 MB zipped. Per-architecture wheels
therefore fit PyPI's default 100 MB per-file limit (the limit itself was not re-checked in this
session). A universal VectorCraft wheel would not fit. Prebuilt CLIs exist for macOS only.

## Second conversion probe (after spec review)

| Route | Command | Result |
|---|---|---|
| pdf → svg with outlined text | `vectorcraft-cli run --in t.pdf --cmd select.all --cmd type.createOutlines --export out.svg` | ok, no `<text>` left |
| multi-page pdf → outlined pdf | same with `--export out.pdf` on a 4-page DesignCraft PDF | ok: 4 pages, 0 `/FontFile`; warning: RGB images in a CMYK document converted to CMYK |
| multi-page pdf import | `vectorcraft-cli info x.pdf` | one artboard per page |
| pptx → single-slide pdf | `deckcraft-cli run --in x.pptx --export one.pdf --export-params '{"slides":[0]}'` | ok, 1 page |
| images → pptx slides | `deckcraft-cli run --cmd 'insert.picture={"path":…,"rect":[0,0,960,540]}' --cmd 'slide.new={"layout":"blank"}' --cmd 'insert.picture=…' --save out.pptx` | ok, 2 slides with pictures; the first slide keeps the default title-slide placeholders, so create blank slides and delete slide 0 |
