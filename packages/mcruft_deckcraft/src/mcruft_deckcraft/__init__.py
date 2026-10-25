# this_file: packages/mcruft_deckcraft/src/mcruft_deckcraft/__init__.py
import json
import math
from pathlib import Path

from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine, page_indexes, pixel_scale
from mcruft.report import Loss, Policy, Report

CONVERSIONS = [("pptx", "deckcraft"), ("deckcraft", "pptx"), ("pptx", "pdf"), ("pptx", "md")]


class DeckcraftEngine(CliEngine):
    PRODUCT = "deckcraft"
    MIN_VERSION = "0.10.0"

    def capabilities(self) -> list[Capability]:
        routes = [("convert", src, dst, "editable") for src, dst in CONVERSIONS]
        routes += [
            ("export_pages", src, dst, policy)
            for src in ("pptx", "deckcraft")
            for dst, policy in (("pdf", "editable"), ("png", "fidelity"))
        ]
        routes += [
            ("build_deck", "png", "pptx", "fidelity"),
            ("inspect", "deckcraft", "deckcraft", "editable"),
        ]
        return [Capability(*row, f"{self.PRODUCT}-cli {self.MIN_VERSION}") for row in routes]

    def inspect(self, path: Path) -> list[tuple[float, float]]:
        path = Path(path)
        if path.suffix.lower() != ".deckcraft":
            return super().inspect(path)
        info = json.loads(self.call(["info", path]))
        return [tuple(map(float, info["slideSize"]))] * len(info["slides"])

    def run(self, op: str, src: Path, dst: Path, *, policy: Policy, **opts) -> Report:
        src, dst = Path(src), Path(dst)
        self.check_route(op, src, dst, policy)
        report = self.report(op, policy, [dst])
        if op == "build_deck":
            images = [Path(p).absolute() for p in opts["images"]]
            if not images:
                raise ValueError("build_deck requires at least one image")
            width, height = opts.get("size", (960, 540))
            if not all(math.isfinite(v) and v > 0 for v in (width, height)):
                raise ValueError("Slide dimensions must be finite and positive")
            args = ["run", "--cmd", "design.slideSize=" + json.dumps({"w": width, "h": height})]
            for image in images:
                args += [
                    "--cmd",
                    'slide.new={"layout":"blank"}',
                    "--cmd",
                    "insert.picture="
                    + json.dumps({"path": str(image), "rect": [0, 0, width, height]}),
                ]
            args += ["--cmd", 'slide.delete={"index":0}', "--save", dst]
            report.losses.append(Loss("raster", "slides are images"))
        elif op == "export_pages":
            info = json.loads(self.call(["info", src]))
            pages = page_indexes(opts.get("pages"), len(info["slides"]))
            if dst.suffix.lower() == ".png":
                scale = pixel_scale(opts.get("dpi", 150))
                report.outputs = []
                for page in pages:
                    out = dst.with_name(f"{dst.stem}-{page:04d}.png")
                    self.call(
                        ["render", src, "--slide", str(page), "--scale", str(scale), out], report
                    )
                    report.outputs.append(out)
                report.losses.append(Loss("raster", "slides rasterised"))
                return report
            args = [
                "run",
                "--in",
                src,
                "--export",
                dst,
                "--export-params",
                json.dumps({"slides": pages}),
            ]
        else:
            args = ["convert", src, dst]
        if dst.suffix.lower() == ".pdf":
            report.losses.append(Loss("raster", "slide art rasterised"))
        self.call(args, report)
        return report


engine = DeckcraftEngine()
