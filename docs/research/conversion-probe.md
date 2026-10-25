---
this_file: docs/research/conversion-probe.md
---

# Conversion probe (verified routes)

Run 2026-10-25 against the installed CLIs: vectorcraft-cli 0.16.0, deckcraft-cli 0.10.0,
photocraft-cli 0.15.1, pdfcraft-cli 0.13.0, designcraft-cli 0.12.0 (macOS). Inputs: a VectorCraft
example SVG, a pydoccraft PPTX fixture, a PNG logo, DesignCraft's built-in `--sample`. "ok" = exit 0
and a non-empty output. Visual fidelity was not scored except where noted.

| Route | Command | Result |
|---|---|---|
| svg → pdf | `vectorcraft-cli convert in.svg out.pdf` | ok |
| svg → png / ai / .vectorcraft | `vectorcraft-cli convert` | ok |
| pdf → svg (editable vector import) | `vectorcraft-cli convert in.pdf out.svg` | ok (text stays `<text>`) |
| pdf → psd | `vectorcraft-cli convert in.pdf out.psd` | ok |
| pptx → pdf / png / md / .deckcraft | `deckcraft-cli convert` | ok |
| .deckcraft → pptx | `deckcraft-cli convert` | ok |
| png → psd, psd → .pcraft / png, png → pdf | `photocraft-cli convert` | ok |
| svg → png (rasterise) | `photocraft-cli convert` | ok |
| pdf page → png | `pdfcraft-cli render in.pdf --page 1 --out p.png` | ok |
| sample → idml / pdf / png / .designcraft | `designcraft-cli run --sample --export out.ext` | ok |
| idml → pptx | `designcraft-cli run --in in.idml --export out.pptx` | ok |
| pptx (from DesignCraft) → pdf | `deckcraft-cli convert` | ok |

## Outlined fonts (the important finding)

- `vectorcraft-cli convert in.svg out.pdf --outline-text` is **byte-identical** to the run without
  the flag; fonts stay embedded. From a `.vectorcraft` input it still embeds fonts in PDF, but SVG
  output does get outlines (no `<text>` left).
- Working route: `vectorcraft-cli run --in X --cmd select.all --cmd type.createOutlines --export out.pdf`
  produces a PDF with **no** `/FontFile` streams.
- This also works as a generic "outline any PDF" step: a DeckCraft-exported PDF run through that
  command produced an outlined PDF whose 96 dpi render differs from the original in 765 of 368 640
  pixels (0.2%, anti-aliasing). Multi-page PDFs were not tested.

## Not tested

Multi-page PDF import into VectorCraft, `.indd` open in DesignCraft, PSD layer round trip,
pdf → docx/pptx in PdfCraft, single-slide PDF export params, any MCP route.
