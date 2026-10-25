# this_file: packages/mcruft/src/mcruft/__init__.py
from pathlib import Path

from .engines.base import Capability, Engine, EngineInfo
from .engines.registry import engines
from .model import Asset, Document, Frame, Media, Page, merge
from .package import load, refresh, save
from .report import (
    EngineFailed,
    EngineUnavailable,
    Loss,
    McruftError,
    PackageError,
    Policy,
    Report,
    UnsupportedRoute,
    UnsupportedSchema,
)

__all__ = [
    "Asset",
    "Capability",
    "Document",
    "Engine",
    "EngineFailed",
    "EngineInfo",
    "EngineUnavailable",
    "Frame",
    "Loss",
    "McruftError",
    "Media",
    "PackageError",
    "Page",
    "Report",
    "UnsupportedRoute",
    "UnsupportedSchema",
    "convert",
    "convert_editable",
    "convert_fidelity",
    "engines",
    "load",
    "merge",
    "new",
    "open",
    "refresh",
    "save",
]


def new(title: str = "") -> Document:
    doc = Document()
    doc.meta["title"] = title
    return doc


def open(path: Path | str) -> Document:
    path = Path(path)
    if path.is_dir():
        return load(path)
    doc = new(path.stem)
    doc.add_file(path)
    return doc


def convert(src: Path | str, dst: Path | str, *, policy: Policy) -> Report:
    raise NotImplementedError("Conversion routes require Task 6")


def convert_editable(src: Path | str, dst: Path | str) -> Report:
    return convert(src, dst, policy="editable")


def convert_fidelity(src: Path | str, dst: Path | str) -> Report:
    return convert(src, dst, policy="fidelity")
