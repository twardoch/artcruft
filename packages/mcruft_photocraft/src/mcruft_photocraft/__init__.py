# this_file: packages/mcruft_photocraft/src/mcruft_photocraft/__init__.py
import json
from pathlib import Path

from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine
from mcruft.report import Loss, Policy, Report

try:
    from .__version__ import __version__ as __version__
except ImportError:
    from importlib.metadata import version

    __version__ = version("mcruft-photocraft")


CONVERSIONS = [
    ("png", "psd", "editable"),
    ("jpg", "psd", "editable"),
    ("psd", "pcraft", "editable"),
    ("psd", "png", "fidelity"),
    ("pcraft", "png", "fidelity"),
    ("png", "pdf", "fidelity"),
    ("jpg", "pdf", "fidelity"),
    ("psd", "pdf", "fidelity"),
    ("pcraft", "pdf", "fidelity"),
    ("png", "psd", "fidelity"),
    ("jpg", "psd", "fidelity"),
    ("psd", "pcraft", "fidelity"),
]


class PhotocraftEngine(CliEngine):
    PRODUCT = "photocraft"
    MIN_VERSION = "0.15.1"

    def capabilities(self) -> list[Capability]:
        routes = [("convert", *row) for row in CONVERSIONS]
        routes += [("inspect", ext, ext, "editable") for ext in ("psd", "pcraft")]
        return [Capability(*row, f"{self.PRODUCT}-cli {self.MIN_VERSION}") for row in routes]

    def inspect(self, path: Path) -> list[tuple[float, float]]:
        path = Path(path)
        if path.suffix.lower() not in (".psd", ".pcraft"):
            return super().inspect(path)
        info = json.loads(self.call(["info", path, "--compact"]))
        dpi = info.get("resolution", 72)
        if dpi <= 0:
            raise ValueError("Image DPI must be positive")
        return [(info["width"] * 72 / dpi, info["height"] * 72 / dpi)]

    def run(self, op: str, src: Path, dst: Path, *, policy: Policy, **opts) -> Report:
        src, dst = Path(src), Path(dst)
        self.check_route(op, src, dst, policy)
        report = self.report(op, policy, [dst])
        if src.suffix.lower() in (".psd", ".pcraft") and dst.suffix.lower() in (".png", ".pdf"):
            report.losses.append(Loss("effects", "layers flattened"))
        self.call(["convert", src, dst], report)
        return report


engine = PhotocraftEngine()
