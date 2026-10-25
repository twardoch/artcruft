# this_file: packages/mcruft/src/mcruft/engines/lib.py
import math
import re
import xml.etree.ElementTree as ET
from importlib.metadata import version
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pypdf import PdfReader, PdfWriter

from ..report import EngineFailed, Loss, Policy, Report, UnsupportedRoute
from .base import Capability, Engine, normalize_format
from .cli import page_indexes, pixel_scale


def svg_size(path: Path) -> tuple[float, float]:
    root = ET.parse(path).getroot()
    dimensions = [root.get(axis, "").strip() for axis in ("width", "height")]
    if "viewBox" in root.attrib and any(not value or value.endswith("%") for value in dimensions):
        values = [float(v) for v in re.split(r"[\s,]+", root.attrib["viewBox"].strip())]
        if len(values) != 4:
            raise UnsupportedRoute("SVG viewBox must have four numbers")
        size = values[2] * 0.75, values[3] * 0.75
    else:
        units = {"": 0.75, "px": 0.75, "pt": 1, "mm": 72 / 25.4, "cm": 72 / 2.54, "in": 72}
        size = []
        for axis in ("width", "height"):
            match = re.fullmatch(
                r"\s*(\d*\.?\d+(?:[eE][+-]?\d+)?)\s*(px|pt|mm|cm|in)?\s*", root.get(axis, "")
            )
            if match is None:
                raise UnsupportedRoute("SVG requires viewBox or absolute width/height")
            size.append(float(match[1]) * units[match[2] or ""])
    if not all(math.isfinite(v) and v > 0 for v in size):
        raise UnsupportedRoute("Page dimensions must be finite and positive")
    return tuple(size)


class LibEngine(Engine):
    name, kind = "lib", "lib"

    def available(self) -> bool:
        return True

    def version(self) -> str:
        return version("pypdf")

    def capabilities(self) -> list[Capability]:
        inspect = [
            Capability("inspect", fmt, fmt, policy, "lib " + library)
            for fmt, library in [
                ("pdf", "pypdf"),
                ("pptx", "python-pptx"),
                ("svg", "XML"),
                ("png", "Pillow"),
                ("jpg", "Pillow"),
                ("jpeg", "Pillow"),
            ]
            for policy in ("editable", "fidelity")
        ]
        raster = [
            Capability("export_pages", fmt, "png", "fidelity", "lib Pillow")
            for fmt in ("png", "jpg", "jpeg")
        ]
        return (
            inspect
            + raster
            + [
                Capability(op, "pdf", "pdf", policy, "lib pypdf")
                for op in ("extract_pages", "combine")
                for policy in ("editable", "fidelity")
            ]
        )

    def inspect(self, path: Path) -> list[tuple[float, float]]:
        path = Path(path)
        match path.suffix.lower():
            case ".pdf":
                sizes = []
                for page in PdfReader(path).pages:
                    size = float(page.mediabox.width), float(page.mediabox.height)
                    sizes.append(size[::-1] if page.rotation % 180 else size)
                return sizes
            case ".pptx":
                prs = Presentation(str(path))
                return [(prs.slide_width / 12700, prs.slide_height / 12700)] * len(prs.slides)
            case ".svg":
                return [svg_size(path)]
            case ".png" | ".jpg" | ".jpeg":
                with Image.open(path) as image:
                    dpi = image.info.get("dpi", (72, 72))
                    if any(d <= 0 for d in dpi):
                        raise UnsupportedRoute("Image DPI must be positive")
                    return [(image.width * 72 / dpi[0], image.height * 72 / dpi[1])]
            case _:
                return super().inspect(path)

    def run(self, op: str, src: Path, dst: Path, *, policy: Policy, **opts) -> Report:
        if (
            not any(
                (c.op, normalize_format(c.src), normalize_format(c.dst), c.policy)
                == (
                    op,
                    normalize_format(Path(src).suffix[1:]),
                    normalize_format(Path(dst).suffix[1:]),
                    policy,
                )
                for c in self.capabilities()
            )
            or op == "inspect"
        ):
            raise UnsupportedRoute(f"lib: {op} ({policy})")
        if op == "export_pages":
            return self.render_image(src, dst, policy, **opts)
        writer = PdfWriter()
        try:
            if op == "extract_pages":
                reader = PdfReader(src)
                indexes = opts["pages"]
                if any(i < 0 or i >= len(reader.pages) for i in indexes):
                    raise IndexError("PDF page index out of range")
                for index in indexes:
                    writer.add_page(reader.pages[index])
            else:
                for path in opts.get("paths", [src]):
                    writer.append(path)
            writer.write(dst)
        except OSError as exc:
            raise EngineFailed(f"lib {op}: {exc}") from exc
        finally:
            writer.close()
        return Report(op, policy, self.name, self.version(), [Path(dst)])

    def render_image(self, src: Path, dst: Path, policy: Policy, **opts) -> Report:
        pages = page_indexes(opts.get("pages"), 1)
        dpi = opts.get("dpi", 150)
        scale = pixel_scale(dpi)
        size = tuple(max(1, round(v * scale)) for v in self.inspect(src)[0])
        outputs = []
        losses = []
        try:
            with Image.open(src) as image:
                if image.info.get("icc_profile"):
                    losses.append(Loss("effects", "ICC profile not kept"))
                rendered = image.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                for page in pages:
                    out = dst.with_name(f"{dst.stem}-{page:04d}.png")
                    rendered.save(out, dpi=(dpi, dpi), icc_profile=None)
                    outputs.append(out)
        except OSError as exc:
            raise EngineFailed(f"lib export_pages: {exc}") from exc
        return Report("export_pages", policy, self.name, self.version(), outputs, losses)


engine = LibEngine()
