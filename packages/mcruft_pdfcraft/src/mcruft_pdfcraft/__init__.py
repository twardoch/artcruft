# this_file: packages/mcruft_pdfcraft/src/mcruft_pdfcraft/__init__.py
from pathlib import Path

from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine, page_indexes, pixel_scale
from mcruft.report import Loss, Policy, Report
from pypdf import PdfReader


class PdfcraftEngine(CliEngine):
    PRODUCT = "pdfcraft"
    MIN_VERSION = "0.13.0"

    def capabilities(self) -> list[Capability]:
        return [
            Capability("export_pages", "pdf", dst, policy, f"{self.PRODUCT}-cli {self.MIN_VERSION}")
            for dst, policy in (("png", "fidelity"), ("pdf", "editable"))
        ]

    def run(self, op: str, src: Path, dst: Path, *, policy: Policy, **opts) -> Report:
        src, dst = Path(src), Path(dst)
        self.check_route(op, src, dst, policy)
        pages = page_indexes(opts.get("pages"), len(PdfReader(src).pages))
        report = self.report(op, policy, [dst])
        if dst.suffix.lower() == ".pdf":
            self.call(
                ["extract", src, "--pages", ",".join(str(i + 1) for i in pages), "--out", dst],
                report,
            )
        else:
            dpi = opts.get("dpi", 150)
            pixel_scale(dpi)
            report.outputs = []
            for page in pages:
                out = dst.with_name(f"{dst.stem}-{page:04d}.png")
                self.call(
                    ["render", src, "--page", str(page + 1), "--dpi", str(dpi), "--out", out],
                    report,
                )
                report.outputs.append(out)
            report.losses.append(Loss("raster", "PDF pages rasterised"))
        return report


engine = PdfcraftEngine()
