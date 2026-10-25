# this_file: packages/mcruft/src/mcruft/editing.py
"""Page edit transactions and optional PDF previews."""

import mimetypes
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .model import Asset, Document, Page, identifier
from .ops import convert, export, joined, owner
from .package import digest, member
from .report import Report, UnsupportedRoute


def previews(doc: Document, root: Path) -> Report:
    reports = []
    pending = []
    with tempfile.TemporaryDirectory(dir=root) as directory:
        for n, page in enumerate(doc.pages):
            previous = doc.assets.get(page.preview)
            source = doc.assets[page.source["asset"]]
            path = member(root, f"previews/page-{n:04d}.pdf")
            valid = (
                previous
                and previous.role == "preview"
                and previous.derived_from == source.id
                and previous.path.is_file()
                and digest(previous.path) == previous.sha256
                and digest(source.path) == source.sha256
            )
            if valid and previous.path == path:
                continue
            staged = Path(directory) / path.name
            if valid:
                shutil.copyfile(previous.path, staged)
                via = previous.via
            else:
                report = export(doc, staged, policy="editable", pages=[n], fonts="embed")
                reports.append(report)
                via = {
                    "engine": report.engine,
                    "engine_version": report.engine_version,
                    "op": "export_pages",
                    "policy": "editable",
                }
            asset = Asset(
                identifier(), path, "application/pdf", digest(staged), "preview", source.id, via
            )
            doc.assets[asset.id] = asset
            page.preview = asset.id
            pending.append((staged, path))
        # Stage every page before replacing paths: reordering must not overwrite another preview.
        for staged, path in pending:
            member(root, "previews").mkdir(parents=True, exist_ok=True)
            os.replace(staged, path)
    referenced = {page.preview for page in doc.pages}
    doc.assets = {
        key: a for key, a in doc.assets.items() if a.role != "preview" or key in referenced
    }
    return joined("save", None, reports, [])


@contextmanager
def edit_in(page: Page, engine: str):
    formats = {
        "photocraft": "psd",
        "vectorcraft": "vectorcraft",
        "deckcraft": "pptx",
        "pdfcraft": "pdf",
    }
    if engine not in formats:
        raise UnsupportedRoute(f"Unknown edit engine: {engine}")
    doc = owner(page)
    index = next(i for i, candidate in enumerate(doc.pages) if candidate is page)
    folder = (
        member(doc.path, "derived") if doc.path else Path(tempfile.mkdtemp(prefix="mcruft-edit-"))
    )
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{identifier()}.{formats[engine]}"
    retained = False
    try:
        with tempfile.TemporaryDirectory(dir=folder) as directory:
            pdf = Path(directory) / "page.pdf"
            export(doc, pdf, policy="editable", pages=[index], fonts="embed")
            if path.suffix == ".pdf":
                pdf.replace(path)
            elif path.suffix == ".pptx":
                export(doc, path, policy="fidelity", pages=[index])
            elif path.suffix == ".vectorcraft":
                svg = Path(directory) / "page.svg"
                convert(pdf, svg, policy="editable")
                convert(svg, path, policy="editable")
            else:
                convert(pdf, path, policy="fidelity")
        before = digest(path)
        yield path
        after = digest(path)
        if after != before:
            asset = Asset(
                identifier(),
                path,
                mimetypes.guess_type(path)[0] or "application/octet-stream",
                after,
                "derived",
                page.source["asset"],
                {"engine": engine, "op": "edit_in"},
            )
            doc.assets[asset.id] = asset
            page.source = {"asset": asset.id, "index": 0}
            page.preview = None
            retained = True
    finally:
        if not retained:
            path.unlink(missing_ok=True)
            if doc.path is None:
                folder.rmdir()
