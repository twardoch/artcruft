# this_file: packages/mcruft/src/mcruft/editing.py
"""Page edit transactions and optional PDF previews."""

import mimetypes
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .engines.base import normalize_format
from .engines.registry import inspect_file
from .model import Asset, Document, Page, identifier
from .ops import convert, export, owner
from .package import digest, member
from .page_ops import joined, run
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
    """Register changed edits before inspection; inspection errors retain the old size and propagate.

    A failed body leaves the document unchanged but preserves a changed working file.
    """
    native = {
        "photocraft": {"png", "jpg", "psd", "pcraft"},
        "vectorcraft": {"svg", "ai", "vectorcraft", "pdf"},
        "deckcraft": {"pptx", "deckcraft"},
        "pdfcraft": {"pdf"},
        "designcraft": {"idml", "designcraft"},
    }
    formats = {
        "photocraft": "psd",
        "vectorcraft": "vectorcraft",
        "deckcraft": "pptx",
        "pdfcraft": "pdf",
        "designcraft": "designcraft",
    }
    if engine not in formats:
        raise UnsupportedRoute(f"Unknown edit engine: {engine}")
    doc = owner(page)
    source = doc.assets[page.source["asset"]]
    fmt = normalize_format(source.path.suffix[1:])
    copied = fmt in native[engine]
    index = page.source["index"] if copied else 0
    folder = (
        member(doc.path, "derived") if doc.path else Path(tempfile.mkdtemp(prefix="mcruft-edit-"))
    )
    folder.mkdir(parents=True, exist_ok=True)
    suffix = source.path.suffix if copied else f".{formats[engine]}"
    path = folder / f"{identifier()}{suffix}"
    retained = False
    try:
        if copied:
            shutil.copyfile(source.path, path)
        elif formats[engine] == "pdf":
            with tempfile.TemporaryDirectory(dir=folder) as directory:
                whole = Path(directory) / "converted.pdf"
                convert(source.path, whole, policy="editable")
                run(
                    "extract_pages",
                    whole,
                    path,
                    "editable",
                    engine="lib",
                    pages=[page.source["index"]],
                )
        else:
            if len(inspect_file(source.path)) != 1:
                raise UnsupportedRoute(f"No single-page editable route: {fmt} -> {formats[engine]}")
            convert(source.path, path, policy="editable")
        before = digest(path)
        try:
            yield path
        finally:
            retained = True
            after = digest(path)
            retained = after != before
        if retained:
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
            page.source = {"asset": asset.id, "index": index}
            page.preview = None
            page.size = inspect_file(path)[index]
    finally:
        if not retained:
            path.unlink(missing_ok=True)
            if doc.path is None:
                folder.rmdir()
