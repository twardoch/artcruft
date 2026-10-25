# this_file: packages/mcruft_designcraft/src/mcruft_designcraft/__init__.py
import json
from pathlib import Path

from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine, page_indexes, pixel_scale
from mcruft.report import Loss, Policy, Report

try:
    from .__version__ import __version__ as __version__
except ImportError:
    from importlib.metadata import version

    __version__ = version("mcruft-designcraft")


FORMATS = ("idml", "designcraft")


class DesigncraftEngine(CliEngine):
    PRODUCT = "designcraft"
    MIN_VERSION = "0.12.0"

    def capabilities(self) -> list[Capability]:
        routes = [
            ("convert", src, dst, "editable")
            for src in FORMATS
            for dst in ("pdf", "pptx", "idml", "designcraft")
        ]
        routes += [
            ("export_pages", src, dst, policy)
            for src in FORMATS
            for dst, policy in (("png", "fidelity"), ("pdf", "editable"))
        ]
        routes += [("inspect", ext, ext, "editable") for ext in FORMATS]
        return [Capability(*row, f"{self.PRODUCT}-cli {self.MIN_VERSION}") for row in routes]

    def inspect(self, path: Path) -> list[tuple[float, float]]:
        path = Path(path)
        if path.suffix.lower()[1:] not in FORMATS:
            return super().inspect(path)
        info = json.loads(self.call(["run", "--in", path, "--cmd", "document.inspect"]))
        pages = sorted(
            (p for spread in info["spreads"] for p in spread["pages"]),
            key=lambda page: page["index"],
        )
        return [(p["bounds"][2] - p["bounds"][0], p["bounds"][3] - p["bounds"][1]) for p in pages]

    def run(self, op: str, src: Path, dst: Path, *, policy: Policy, **opts) -> Report:
        src, dst = Path(src), Path(dst)
        self.check_route(op, src, dst, policy)
        report = self.report(op, policy, [dst])
        args = ["run", "--in", src]
        if op == "export_pages":
            pages = page_indexes(opts.get("pages"), len(self.inspect(src)))
            if dst.suffix.lower() == ".png":
                scale = pixel_scale(opts.get("dpi", 150))
                # PNG export always includes bleed; remove it in this unsaved session.
                args += ["--cmd", 'layout.documentSetup={"bleed":0}']
                report.outputs = []
                for page in pages:
                    out = dst.with_name(f"{dst.stem}-{page:04d}.png")
                    # --page is 0-based: sample exports match --all-pages page-(N+1).
                    self.call(
                        [*args, "--page", str(page), "--scale", str(scale), "--export", out], report
                    )
                    report.outputs.append(out)
                report.losses.append(Loss("raster", "pages rasterised"))
                return report
            # PDF options use 1-based page positions, preserving order and duplicates.
            args += ["--pdf-options", json.dumps({"pages": [i + 1 for i in pages]})]
        self.call([*args, "--export", dst], report)
        return report


engine = DesigncraftEngine()
