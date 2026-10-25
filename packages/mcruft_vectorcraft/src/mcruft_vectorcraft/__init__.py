# this_file: packages/mcruft_vectorcraft/src/mcruft_vectorcraft/__init__.py
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine, page_indexes, pixel_scale
from mcruft.report import Loss, Policy, Report
from pypdf import PdfReader, PdfWriter

CONVERSIONS = [
    ("svg", "pdf", "editable"),
    ("svg", "png", "fidelity"),
    ("svg", "ai", "editable"),
    ("svg", "vectorcraft", "editable"),
    ("pdf", "svg", "editable"),
    ("pdf", "psd", "fidelity"),
    ("vectorcraft", "pdf", "editable"),
    ("vectorcraft", "svg", "editable"),
    ("vectorcraft", "png", "fidelity"),
]


class VectorcraftEngine(CliEngine):
    PRODUCT = "vectorcraft"
    MIN_VERSION = "0.16.0"

    def capabilities(self) -> list[Capability]:
        routes = [("convert", *row) for row in CONVERSIONS]
        routes += [
            ("outline_text", src, dst, "fidelity")
            for src in ("pdf", "svg", "vectorcraft", "ai")
            for dst in ("pdf", "svg")
        ]
        routes += [("export_pages", src, "pdf", "editable") for src in ("vectorcraft", "svg", "ai")]
        routes += [("inspect", ext, ext, "editable") for ext in ("vectorcraft", "ai", "eps")]
        return [Capability(*row, f"{self.PRODUCT}-cli {self.MIN_VERSION}") for row in routes]

    def inspect(self, path: Path) -> list[tuple[float, float]]:
        path = Path(path)
        if path.suffix.lower() not in (".vectorcraft", ".ai", ".eps"):
            return super().inspect(path)
        info = json.loads(self.call(["info", path]))
        # VectorCraft info uses [x, y, width, height], unlike DesignCraft bounds.
        return [(float(a["rect"][2]), float(a["rect"][3])) for a in info["artboards"]]

    def run(self, op: str, src: Path, dst: Path, *, policy: Policy, **opts) -> Report:
        src, dst = Path(src), Path(dst)
        self.check_route(op, src, dst, policy)
        report = self.report(op, policy, [dst])
        args = ["convert", src, dst]
        if op == "outline_text":
            args = [
                "run",
                "--in",
                src,
                "--cmd",
                "select.all",
                "--cmd",
                "type.createOutlines",
                "--export",
                dst,
            ]
            report.losses.append(
                Loss(
                    "layout",
                    "re-imported via VectorCraft: links, annotations and forms may be dropped",
                )
            )
        elif op == "export_pages":
            count = len(json.loads(self.call(["info", src]))["artboards"])
            pages = page_indexes(opts.get("pages"), count)
            if len(set(pages)) != len(pages):
                # --range drops duplicates; join single-artboard exports to retain them.
                with TemporaryDirectory(dir=dst.parent) as directory, PdfWriter() as writer:
                    for index, page in enumerate(pages):
                        part = Path(directory) / f"{index}.pdf"
                        self.call([*args[:2], part, "--artboard", str(page)], report)
                        writer.append(PdfReader(part))
                    writer.write(dst)
                return report
            args += (
                ["--artboard", str(pages[0])]
                if len(pages) == 1
                else ["--range", ",".join(str(i + 1) for i in pages)]
            )
        elif dst.suffix.lower() == ".png":
            args += ["--scale", str(pixel_scale(opts.get("dpi", 150)))]
        if dst.suffix.lower() in (".png", ".psd"):
            report.losses.append(Loss("raster", "vector artwork rasterised"))
        self.call(args, report)
        return report


engine = VectorcraftEngine()
