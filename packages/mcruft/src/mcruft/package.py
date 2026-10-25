# this_file: packages/mcruft/src/mcruft/package.py
import hashlib
import json
import os
import shutil
import tempfile
import warnings
from copy import deepcopy
from dataclasses import asdict, replace
from importlib.metadata import version
from itertools import count
from pathlib import Path, PurePosixPath

from .model import Asset, Document, Media, Page, timestamp
from .report import PackageError, Report, UnsupportedSchema


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def member(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if not name or relative.is_absolute() or ".." in relative.parts or "\\" in name:
        raise PackageError(f"Unsafe package path: {name}")
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise PackageError(f"Symlink in package path: {name}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise PackageError(f"Path outside package: {name}")
    return path


def copy_asset(asset: Asset, root: Path) -> Path:
    folder = {"source": "assets", "derived": "derived", "preview": "previews"}[asset.role]
    directory = member(root, folder)
    directory.mkdir(parents=True, exist_ok=True)
    source = Path(asset.path).absolute()
    if source.is_relative_to(root):
        member(root, source.relative_to(root).as_posix())
        return source
    for number in count():
        suffix = f"-{number}" if number else ""
        target = member(root, f"{folder}/{source.stem}{suffix}{source.suffix}")
        try:
            stream = target.open("xb")
        except FileExistsError:
            continue
        try:
            with stream, source.open("rb") as incoming:
                shutil.copyfileobj(incoming, stream)
        except BaseException:
            target.unlink()
            raise
        return target


def save(doc: Document, path: Path | str | None = None, *, previews: bool = False) -> Report:
    if path is None and doc.path is None:
        raise PackageError("An unsaved document needs a package path")
    root = Path(path if path is not None else doc.path).absolute()
    if root.is_symlink():
        raise PackageError("Package root must not be a symlink")
    try:
        root.mkdir(parents=True, exist_ok=True)
        manifest = member(root, "manifest.json")
        staged = Document(
            deepcopy(doc.meta), dict(doc.assets), deepcopy(doc.pages), doc.media, doc.path
        )
        report = Report("save")
        if previews:
            from .editing import previews as generate_previews

            report = generate_previews(staged, root)
        referenced = {page.preview for page in staged.pages}
        staged.assets = {
            key: asset
            for key, asset in staged.assets.items()
            if asset.role != "preview" or key in referenced
        }
        assets = {
            key: replace(asset, path=copy_asset(asset, root))
            for key, asset in staged.assets.items()
        }
        meta = {**doc.meta, "modified": timestamp()}
        data = {
            "schema_version": 1,
            "generator": f"mcruft {version('mcruft')}",
            "meta": meta,
            "assets": {
                key: {k: v for k, v in asdict(asset).items() if k != "id"}
                for key, asset in assets.items()
            },
            "pages": [
                {k: v for k, v in asdict(page).items() if k != "frames"} for page in staged.pages
            ],
            "media": [asdict(m) for m in doc.media],
        }
        for item in data["assets"].values():
            item["path"] = item["path"].relative_to(root).as_posix()
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", dir=root, delete=False, encoding="utf-8"
            ) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, indent=2)
                stream.write("\n")
            os.replace(temporary, manifest)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PackageError(f"Cannot save package {root}: {exc}") from exc
    doc.path, doc.assets, doc.meta = root, assets, meta
    for page, staged_page in zip(doc.pages, staged.pages):
        page.preview = staged_page.preview
    report.outputs = [manifest]
    return report


def load(path: Path | str) -> Document:
    root = Path(path).absolute()
    if root.is_symlink():
        raise PackageError("Package root must not be a symlink")
    try:
        data = json.loads(member(root, "manifest.json").read_text(encoding="utf-8"))
        if data["schema_version"] != 1:
            raise UnsupportedSchema(f"Unknown schema_version: {data['schema_version']}")
        assets = {
            key: Asset(id=key, **{**value, "path": member(root, value["path"])})
            for key, value in data["assets"].items()
        }
        pages = [Page(**{**p, "size": tuple(p["size"]), "frames": []}) for p in data["pages"]]
        for page in pages:
            if (
                page.source["asset"] not in assets
                or not isinstance(page.source["index"], int)
                or page.source["index"] < 0
                or (page.preview is not None and page.preview not in assets)
            ):
                raise PackageError(f"Invalid page references: {page.id}")
        media = [Media(**m) for m in data["media"]]
        if any(m.asset not in assets for m in media):
            raise PackageError("Invalid media asset reference")
        for asset in assets.values():
            if digest(asset.path) != asset.sha256:
                warnings.warn(f"sha256 mismatch: {asset.path.name}", UserWarning, stacklevel=2)
        return Document(data["meta"], assets, pages, media, root)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise PackageError(f"Cannot load package {root}: {exc}") from exc


def refresh(doc: Document) -> Report:
    report = Report("refresh")
    try:
        hashes = {key: digest(asset.path) for key, asset in doc.assets.items()}
    except OSError as exc:
        raise PackageError(f"Cannot refresh assets: {exc}") from exc
    changed = {key for key, asset in doc.assets.items() if asset.sha256 != hashes[key]}
    for page in doc.pages:
        preview = doc.assets.get(page.preview)
        if (
            page.source["asset"] in changed
            or page.preview in changed
            or (preview and preview.derived_from in changed)
        ):
            page.preview = None
    for key in changed:
        doc.assets[key].sha256 = hashes[key]
        report.warnings.append(f"Refreshed changed asset: {key}; stale previews dropped")
    return report
