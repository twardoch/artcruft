# this_file: packages/mcruft/src/mcruft/page_ops.py
"""Ordered page pipelines and shared operation boundaries."""

import os
from dataclasses import replace
from itertools import groupby
from pathlib import Path
from tempfile import TemporaryDirectory

from .engines import registry
from .engines.base import Engine, normalize_format
from .engines.cli import pixel_scale
from .model import Document, Page
from .report import PackageError, Policy, Report, UnsupportedRoute

RASTER = {"png", "jpg", "psd", "pcraft"}


def destination(path: Path | str, doc: Document | None = None) -> Path:
    dst = Path(path).absolute()
    if not dst.parent.is_dir():
        raise PackageError(f"Destination parent directory is missing: {dst.parent}")
    if doc and any(dst.resolve() == a.path.resolve() for a in doc.assets.values()):
        raise PackageError(f"Destination is a document asset: {dst}")
    return dst


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


def convert_pages(src: Path, dst: Path, policy: Policy, backend: Engine) -> Report:
    pages = list(range(len(registry.inspect_file(src))))
    outputs = (
        [dst.with_name(f"{dst.stem}-{i:04d}.png") for i in pages]
        if dst.suffix.lower() == ".png" and len(pages) > 1
        else [dst]
    )
    with TemporaryDirectory(dir=dst.parent) as directory:
        temporary = Path(directory) / f"pages{dst.suffix}"
        report = backend.run("export_pages", src, temporary, policy=policy, pages=pages)
        for source, target in zip(report.outputs, outputs, strict=True):
            os.replace(source, target)
    return replace(report, op="convert", outputs=outputs)


def group_pdf(doc: Document, pages: list[Page], dst: Path, policy: Policy) -> list[Report]:
    source = doc.assets[pages[0].source["asset"]].path
    indexes = [p.source["index"] for p in pages]
    fmt = normalize_format(source.suffix[1:])
    if fmt == "pdf":
        return [run("extract_pages", source, dst, "editable", pages=indexes)]
    policies = ["fidelity"] if fmt in RASTER else list(dict.fromkeys([policy, "editable"]))
    for candidate in policies:
        try:
            backend, _ = registry.route("export_pages", fmt, "pdf", candidate)
        except UnsupportedRoute:
            continue
        report = backend.run("export_pages", source, dst, policy=candidate, pages=indexes)
        if candidate != policy and fmt not in RASTER:
            report.warnings.append(f"{fmt}: no {policy} page export; used {candidate}")
        return [report]
    if len(registry.inspect_file(source)) != 1:
        raise UnsupportedRoute(f"No PDF page export for multi-page {fmt} ({policy})")
    for candidate in policies:
        try:
            backend, _ = registry.route("convert", fmt, "pdf", candidate)
        except UnsupportedRoute:
            continue
        whole = dst.with_name(f"{dst.stem}-whole.pdf")
        return [
            backend.run("convert", source, whole, policy=candidate),
            run("extract_pages", whole, dst, "editable", pages=indexes),
        ]
    raise UnsupportedRoute(f"No PDF export route for {fmt}; tried policies: {policies}")


def pdf_pages(
    doc: Document, pages: list[Page], dst: Path, fonts: str, policy: Policy
) -> list[Report]:
    reports, parts = [], []
    with TemporaryDirectory(dir=dst.parent) as directory:
        for n, (_, group) in enumerate(groupby(pages, lambda p: p.source["asset"])):
            part = Path(directory) / f"group-{n}.pdf"
            reports.extend(group_pdf(doc, list(group), part, policy))
            parts.append(part)
        result = Path(directory) / "combined.pdf"
        reports.append(run("combine", parts[0], result, "editable", paths=parts))
        # Raster PDF routes flatten text already; VectorCraft cannot outline image-only pages.
        raster_only = all(
            normalize_format(doc.assets[p.source["asset"]].path.suffix[1:]) in RASTER for p in pages
        )
        if fonts == "outline" and not raster_only:
            outlined = Path(directory) / "outlined.pdf"
            reports.append(run("outline_text", result, outlined, "fidelity"))
            result = outlined
        os.replace(result, dst)
    return reports


def png_pages(
    doc: Document, pages: list[Page], dst: Path, dpi: int
) -> tuple[list[Report], list[Path]]:
    pixel_scale(dpi)
    outputs = [
        destination(dst.with_name(f"{dst.stem}-{n:04d}.png"), doc) for n in range(len(pages))
    ]
    reports = []
    with TemporaryDirectory(dir=dst.parent) as directory:
        for n, page in enumerate(pages):
            source = doc.assets[page.source["asset"]].path
            temporary = Path(directory) / f"page-{n}.png"
            try:
                backend, _ = registry.route("export_pages", source.suffix[1:], "png", "fidelity")
            except UnsupportedRoute:
                if len(registry.inspect_file(source)) != 1:
                    raise
                report = run("convert", source, temporary, "fidelity", dpi=dpi)
            else:
                report = backend.run(
                    "export_pages",
                    source,
                    temporary,
                    policy="fidelity",
                    pages=[page.source["index"]],
                    dpi=dpi,
                )
            os.replace(report.outputs[0], outputs[n])
            reports.append(report)
    return reports, outputs
