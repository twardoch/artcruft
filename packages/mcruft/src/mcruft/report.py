# this_file: packages/mcruft/src/mcruft/report.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Policy = Literal["editable", "fidelity"]


class McruftError(Exception):
    """Base error for mcruft operations."""


class UnsupportedRoute(McruftError):
    """No engine supports the requested operation and policy."""


class EngineUnavailable(McruftError):
    """The requested backend is not installed."""


class EngineFailed(McruftError):
    """A backend failed; CLI errors include argv and stderr."""


class UnsupportedSchema(McruftError):
    """The package uses an unknown manifest schema."""


class PackageError(McruftError):
    """The package cannot be safely read or written."""


@dataclass
class Loss:
    kind: Literal["raster", "fonts", "layout", "effects", "media", "unsupported"]
    detail: str
    page: int | None = None


@dataclass
class Report:
    op: str
    policy: Policy | None = None
    engine: str = "mcruft"
    engine_version: str | None = None
    outputs: list[Path] = field(default_factory=list)
    losses: list[Loss] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
