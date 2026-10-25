# this_file: packages/mcruft/src/mcruft/engines/libs_resvg.py
"""Optional static SVG rasterization with resvg-py."""

import importlib.util
from importlib.metadata import version
from pathlib import Path

from ..report import EngineFailed, Loss, Policy, Report
from .base import Capability
from .cli import page_indexes, pixel_scale


def capabilities() -> list[Capability]:
    if importlib.util.find_spec("resvg_py") is None:
        return []
    return [
        Capability(op, "svg", "png", "fidelity", f"lib resvg-py {version('resvg-py')}")
        for op in ("convert", "export_pages")
    ]


def render(op: str, src: Path, dst: Path, policy: Policy, **opts) -> Report:
    import resvg_py

    pixel_scale(opts.get("dpi", 150))  # validates dpi
    indexes = page_indexes(opts.get("pages"), 1) if op == "export_pages" else [0]
    # CSS px are 1/96 inch: zoom scales both pixel and physical SVG dimensions once.
    scale = opts.get("dpi", 150) / 96
    outputs = []
    try:
        png = resvg_py.svg_to_bytes(svg_path=str(src), zoom=scale, dpi=96)
        for index in indexes:
            out = dst if op == "convert" else dst.with_name(f"{dst.stem}-{index:04d}.png")
            out.write_bytes(png)
            outputs.append(out)
    except (OSError, ValueError) as exc:
        raise EngineFailed(f"lib resvg-py {op}: {exc}") from exc
    return Report(
        op,
        policy,
        "lib",
        version("resvg-py"),
        outputs,
        [Loss("raster", "SVG rasterised")],
        ["SVG fonts are resolved from the system; results depend on installed fonts."],
    )
