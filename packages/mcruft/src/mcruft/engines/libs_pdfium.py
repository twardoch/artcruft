# this_file: packages/mcruft/src/mcruft/engines/libs_pdfium.py
"""Optional PDF rasterization; PDFium is not thread-safe, even across documents."""

import importlib.util
from contextlib import closing
from importlib.metadata import version
from pathlib import Path
from threading import Lock

from ..report import EngineFailed, Loss, Policy, Report
from .base import Capability
from .cli import page_indexes, pixel_scale

PDFIUM_LOCK = Lock()


def capabilities() -> list[Capability]:
    if importlib.util.find_spec("pypdfium2") is None:
        return []
    return [
        Capability(
            "export_pages", "pdf", "png", "fidelity", f"lib pypdfium2 {version('pypdfium2')}"
        )
    ]


def export_pages(src: Path, dst: Path, policy: Policy, **opts) -> Report:
    dpi = opts.get("dpi", 150)
    scale = pixel_scale(dpi)
    outputs = []
    with PDFIUM_LOCK:
        # Import initializes PDFium; creation, rendering and cleanup all need the lock.
        import pypdfium2 as pdfium

        try:
            with pdfium.PdfDocument(src) as document:
                for index in page_indexes(opts.get("pages"), len(document)):
                    out = dst.with_name(f"{dst.stem}-{index:04d}.png")
                    with (
                        closing(document[index]) as page,
                        closing(page.render(scale=scale)) as bitmap,
                        bitmap.to_pil() as image,
                    ):
                        image.save(out, dpi=(dpi, dpi))
                    outputs.append(out)
        except (OSError, pdfium.PdfiumError) as exc:
            raise EngineFailed(f"lib pypdfium2 export_pages: {exc}") from exc
    return Report(
        "export_pages",
        policy,
        "lib",
        version("pypdfium2"),
        outputs,
        [Loss("raster", "PDF pages rasterised")],
    )
