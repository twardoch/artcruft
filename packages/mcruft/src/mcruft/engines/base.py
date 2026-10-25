# this_file: packages/mcruft/src/mcruft/engines/base.py
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..report import Policy, Report, UnsupportedRoute


@dataclass(frozen=True)
class Capability:
    op: str
    src: str
    dst: str
    policy: Policy
    verified_with: str | None = None
    note: str = ""


class Engine:
    name: str
    kind: Literal["cli", "mcp", "native", "lib"]

    def available(self) -> bool:
        return False

    def version(self) -> str | None:
        return None

    def capabilities(self) -> list[Capability]:
        return []

    def run(self, op: str, src: Path, dst: Path, *, policy: Policy, **opts) -> Report:
        raise UnsupportedRoute(f"{self.name}: {op} {policy}")

    def inspect(self, path: Path) -> list[tuple[float, float]]:
        raise UnsupportedRoute(f"{self.name}: cannot inspect {path.suffix}")


@dataclass
class EngineInfo:
    name: str
    kind: str
    available: bool
    version: str | None
    capabilities: list[Capability]
