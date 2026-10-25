# this_file: packages/mcruft/src/mcruft/ops.py
"""Capability-routed conversion and ordered page export."""

import os
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from .engines import registry
from .engines.base import normalize_format
from .engines.cli import page_indexes, pixel_scale
from .model import Document, Page
from .page_ops import RASTER, destination, joined, pdf_pages, png_pages, run
from .report import Policy, Report, UnsupportedRoute


def check_policy(policy: Policy) -> None:
    if policy not in ("editable", "fidelity"):
        raise ValueError(f"Unknown policy: {policy}")


def convert(src: Path | str, dst: Path | str, *, policy: Policy) -> Report:
    check_policy(policy)
    src, dst = Path(src).absolute(), Path(dst).absolute()
    if src.resolve() == dst.resolve():
        raise ValueError("Source and destination resolve to the same path")
    destination(dst)
    s, d = normalize_format(src.suffix[1:]), normalize_format(dst.suffix[1:])
    route_policy = "fidelity" if s in RASTER and d == "pdf" else policy
    try:
        backend, _ = registry.route("convert", s, d, route_policy)
    except UnsupportedRoute:
        backend = None
    if backend is not None:
        return replace(backend.run("convert", src, dst, policy=route_policy), policy=policy)
    if policy == "fidelity" and d in ("pdf", "svg"):
        try:
            if s == d:
                return joined("convert", policy, [run("outline_text", src, dst, policy)], [dst])
            try:
                editable, _ = registry.route("convert", s, d, "editable")
                middle = d
            except UnsupportedRoute:
                if d != "svg":
                    raise
                editable, _ = registry.route("convert", s, "pdf", "editable")
                middle = "pdf"
            outline, _ = registry.route("outline_text", middle, d, "fidelity")
        except UnsupportedRoute:
            pass
        else:
            with TemporaryDirectory(dir=dst.parent) as directory:
                intermediate = Path(directory) / f"editable.{middle}"
                first = editable.run("convert", src, intermediate, policy="editable")
                last = outline.run("outline_text", intermediate, dst, policy="fidelity")
                return joined("convert", policy, [first, last], [dst])
    existing = sorted(
        {
            f"{e.name}: {c.op} ({c.policy})"
            for e in registry.discover()
            for c in e.capabilities()
            if (c.src, c.dst) == (s, d)
        }
    )
    raise UnsupportedRoute(f"No route: {s} -> {d} ({policy}); existing routes: {existing}")


def export(
    doc: Document,
    path: Path | str,
    *,
    policy: Policy,
    pages=None,
    fonts: str | None = None,
    dpi: int = 150,
) -> Report:
    check_policy(policy)
    if fonts is None:
        fonts = "outline" if policy == "fidelity" else "embed"
    if fonts not in ("embed", "outline"):
        raise ValueError("fonts must be embed or outline")
    pixel_scale(dpi)
    selected = [doc.pages[i] for i in page_indexes(pages, len(doc.pages))]
    dst = destination(path, doc)
    match dst.suffix.lower():
        case ".pdf":
            reports = pdf_pages(doc, selected, dst, fonts, policy)
            outputs = [dst]
        case ".png":
            if policy != "fidelity":
                raise UnsupportedRoute("raster targets accept only fidelity")
            reports, outputs = png_pages(doc, selected, dst, dpi)
        case ".svg":
            if len(selected) != 1:
                raise UnsupportedRoute("SVG export requires exactly one page")
            with TemporaryDirectory(dir=dst.parent) as directory:
                pdf = Path(directory) / "page.pdf"
                reports = pdf_pages(doc, selected, pdf, "embed", "editable")
                reports.append(convert(pdf, dst, policy=policy))
            outputs = [dst]
        case ".pptx":
            if policy == "editable":
                raise UnsupportedRoute("no verified pdf->editable-slide route")
            with TemporaryDirectory(dir=dst.parent) as directory:
                reports, images = png_pages(doc, selected, Path(directory) / "slide.png", dpi)
                reports.append(
                    run("build_deck", images[0], dst, policy, images=images, size=selected[0].size)
                )
            outputs = [dst]
        case _:
            raise UnsupportedRoute(f"Unsupported export suffix: {dst.suffix}")
    return joined("export", policy, reports, outputs)


def owner(page: Page) -> Document:
    doc = getattr(page, "_document", lambda: None)()
    if doc is None:
        raise ValueError("Page must belong to a document")
    return doc


def render(page: Page, path: Path | str, dpi: int = 150) -> Report:
    doc = owner(page)
    dst = destination(path, doc)
    with TemporaryDirectory(dir=dst.parent) as directory:
        reports, outputs = png_pages(doc, [page], Path(directory) / "render.png", dpi)
        os.replace(outputs[0], dst)
    return joined("export", "fidelity", reports, [dst])
