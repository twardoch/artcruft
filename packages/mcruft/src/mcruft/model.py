# this_file: packages/mcruft/src/mcruft/model.py
from __future__ import annotations

import mimetypes
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from .report import Policy, Report


def identifier() -> str:
    return uuid4().hex


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Asset:
    id: str
    path: Path
    media_type: str
    sha256: str
    role: Literal["source", "derived", "preview"] = "source"
    derived_from: str | None = None
    via: dict[str, str] | None = None


@dataclass
class Frame:
    id: str
    kind: Literal["text", "vector", "image", "media", "group"]
    bbox: tuple[float, float, float, float]
    rotation: float = 0
    asset: str | None = None
    text: str | None = None
    children: list[Frame] = field(default_factory=list)
    time: tuple[float, float] | None = None


@dataclass
class Page:
    id: str
    size: tuple[float, float]
    source: dict[str, str | int]
    preview: str | None = None
    frames: list[Frame] = field(default_factory=list)

    def render(self, path: Path | str, dpi: int = 150) -> Report:
        from .ops import render

        return render(self, path, dpi)

    def edit_in(self, engine: str):
        from .editing import edit_in

        return edit_in(self, engine)


@dataclass
class Media:
    id: str
    asset: str
    kind: Literal["video", "audio"]
    duration_s: float


@dataclass
class Document:
    meta: dict[str, str] = field(
        default_factory=lambda: {"title": "", "created": timestamp(), "modified": timestamp()}
    )
    assets: dict[str, Asset] = field(default_factory=dict)
    pages: list[Page] = field(default_factory=list)
    media: list[Media] = field(default_factory=list)
    path: Path | None = None

    def __post_init__(self) -> None:
        for page in self.pages:
            page._document = self

    def add_file(self, path: Path | str) -> list[Page]:
        from .engines.registry import inspect_file
        from .package import copy_asset, digest

        path = Path(path).absolute()
        sizes = inspect_file(path)
        asset = Asset(
            identifier(),
            path,
            mimetypes.guess_type(path)[0] or "application/octet-stream",
            digest(path),
        )
        if self.path is not None:
            asset.path = copy_asset(asset, self.path)
        pages = [
            Page(identifier(), size, {"asset": asset.id, "index": i})
            for i, size in enumerate(sizes)
        ]
        self.assets[asset.id] = asset
        self.pages.extend(pages)
        self.__post_init__()
        return pages

    def remove_pages(self, indexes: list[int]) -> None:
        if any(i < 0 or i >= len(self.pages) for i in indexes):
            raise IndexError("Page index out of range")
        self.pages[:] = [p for i, p in enumerate(self.pages) if i not in set(indexes)]

    def move_page(self, i: int, to: int) -> None:
        if not (0 <= i < len(self.pages) and 0 <= to < len(self.pages)):
            raise IndexError("Page index out of range")
        self.pages.insert(to, self.pages.pop(i))

    def split(self) -> list[Document]:
        return [
            Document(
                deepcopy(self.meta),
                deepcopy(self.assets),
                [deepcopy(page, {id(self): None})],
                deepcopy(self.media),
            )
            for page in self.pages
        ]

    def save(self, path: Path | str | None = None, previews: bool = False) -> Report:
        from .package import save

        return save(self, path, previews=previews)

    def refresh(self) -> Report:
        from .package import refresh

        return refresh(self)

    def export(
        self,
        path: Path | str,
        *,
        policy: Policy,
        pages: list[int] | None = None,
        fonts: str | None = None,
        dpi: int = 150,
    ) -> Report:
        from .ops import export

        return export(self, path, policy=policy, pages=pages, fonts=fonts, dpi=dpi)


def merge(docs: list[Document]) -> Document:
    result = Document()
    for doc in docs:
        copy = deepcopy(doc)
        mapping = {key: identifier() for key in copy.assets}
        for key, asset in copy.assets.items():
            asset.id = mapping[key]
            asset.derived_from = mapping.get(asset.derived_from)
            result.assets[asset.id] = asset
        for page in copy.pages:
            page.id = identifier()
            page.source["asset"] = mapping[page.source["asset"]]
            page.preview = mapping.get(page.preview)
        for media in copy.media:
            media.id, media.asset = identifier(), mapping[media.asset]
        result.pages.extend(copy.pages)
        result.media.extend(copy.media)
    result.__post_init__()
    return result
