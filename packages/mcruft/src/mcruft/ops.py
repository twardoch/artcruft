# this_file: packages/mcruft/src/mcruft/ops.py
"""Capability-routed conversion and ordered page export."""

import os
from itertools import groupby
from pathlib import Path
from tempfile import TemporaryDirectory

from .engines import registry
from .engines.cli import page_indexes, pixel_scale
from .model import Document, Page
from .report import Policy, Report, UnsupportedRoute


def check_policy(policy: Policy) -> None:
    if policy not in ("editable", "fidelity"):
        raise ValueError(f"Unknown policy: {policy}")


def run(op: str, src: Path, dst: Path, policy: Policy, *, engine=None, **opts) -> Report:
    backend, _ = registry.route(op, src.suffix.lower()[1:], dst.suffix.lower()[1:], policy, engine)
    return backend.run(op, src.absolute(), dst.absolute(), policy=policy, **opts)


def joined(op: str, policy: Policy | None, reports: list[Report], outputs: list[Path]) -> Report:
    return Report(
        op,
        policy,
        "+".join(r.engine for r in reports) or "mcruft",
        "+".join(r.engine_version or "unknown" for r in reports) or None,
        outputs,
        [loss for r in reports for loss in r.losses],
        [warning for r in reports for warning in r.warnings],
    )


def convert(src: Path | str, dst: Path | str, *, policy: Policy) -> Report:
    check_policy(policy)
    src, dst = Path(src).absolute(), Path(dst).absolute()
    s, d = src.suffix.lower()[1:], dst.suffix.lower()[1:]
    try:
        backend, _ = registry.route("convert", s, d, policy)
    except UnsupportedRoute:
        backend = None
    if backend is not None:
        return backend.run("convert", src, dst, policy=policy)
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


def pdf_pages(doc: Document, pages: list[Page], dst: Path, fonts: str) -> list[Report]:
    reports, parts = [], []
    with TemporaryDirectory(dir=dst.parent) as directory:
        for n, (asset_id, group) in enumerate(groupby(pages, lambda p: p.source["asset"])):
            asset = doc.assets[asset_id]
            part = Path(directory) / f"group-{n}.pdf"
            op = "extract_pages" if asset.path.suffix.lower() == ".pdf" else "export_pages"
            reports.append(
                run(
                    op,
                    asset.path,
                    part,
                    "editable",
                    engine="lib" if op == "extract_pages" else None,
                    pages=[p.source["index"] for p in group],
                )
            )
            parts.append(part)
        reports.append(run("combine", parts[0], dst, "editable", engine="lib", paths=parts))
        if fonts == "outline":
            outlined = Path(directory) / "outlined.pdf"
            reports.append(run("outline_text", dst, outlined, "fidelity"))
            os.replace(outlined, dst)
    return reports


def png_pages(
    doc: Document, pages: list[Page], dst: Path, dpi: int
) -> tuple[list[Report], list[Path]]:
    pixel_scale(dpi)
    reports, outputs = [], []
    with TemporaryDirectory(dir=dst.parent) as directory:
        for n, page in enumerate(pages):
            source = doc.assets[page.source["asset"]].path
            temporary = Path(directory) / f"page-{n}.png"
            report = run(
                "export_pages", source, temporary, "fidelity", pages=[page.source["index"]], dpi=dpi
            )
            target = dst.with_name(f"{dst.stem}-{n:04d}.png")
            os.replace(report.outputs[0], target)
            reports.append(report)
            outputs.append(target)
    return reports, outputs


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
    dst = Path(path).absolute()
    match dst.suffix.lower():
        case ".pdf":
            reports = pdf_pages(doc, selected, dst, fonts)
            outputs = [dst]
        case ".png":
            reports, outputs = png_pages(doc, selected, dst, dpi)
        case ".svg":
            if len(selected) != 1:
                raise UnsupportedRoute("SVG export requires exactly one page")
            with TemporaryDirectory(dir=dst.parent) as directory:
                pdf = Path(directory) / "page.pdf"
                reports = pdf_pages(doc, selected, pdf, "embed")
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
    dst = Path(path).absolute()
    reports, outputs = png_pages(doc, [page], dst.with_suffix(".png"), dpi)
    os.replace(outputs[0], dst)
    return joined("export", "fidelity", reports, [dst])
