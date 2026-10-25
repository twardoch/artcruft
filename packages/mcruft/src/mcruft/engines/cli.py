# this_file: packages/mcruft/src/mcruft/engines/cli.py
import importlib
import json
import math
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from ..report import EngineFailed, EngineUnavailable, Policy, Report, UnsupportedRoute
from .base import Engine


def run_cli(argv: list[str | Path], timeout: float = 600) -> subprocess.CompletedProcess:
    args = [str(arg.absolute()) if isinstance(arg, Path) else arg for arg in argv]
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        tail = getattr(exc, "stderr", "") or str(exc)
        if isinstance(tail, bytes):
            tail = tail.decode(errors="replace")
        raise EngineFailed(f"{shlex.join(args)}\n{tail[-4000:]}") from exc


def parse_version(text: str) -> str:
    match = re.search(r"\b\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?", text)
    if match is None:
        raise EngineFailed(f"No version number in CLI output: {text[:200]}")
    return match[0]


def page_indexes(pages: list[int] | None, count: int) -> list[int]:
    indexes = list(range(count)) if pages is None else list(pages)
    if not indexes:
        raise ValueError("Select at least one page")
    if any(type(i) is not int or i < 0 or i >= count for i in indexes):
        raise IndexError(f"Page indexes must be integers in 0..{count - 1}")
    return indexes


def pixel_scale(dpi: float) -> float:
    if not math.isfinite(dpi) or dpi <= 0:
        raise ValueError("DPI must be finite and positive")
    return dpi / 72


def json_warnings(value) -> list[str]:
    if isinstance(value, list):
        return [warning for item in value for warning in json_warnings(item)]
    if not isinstance(value, dict):
        return []
    return [
        warning
        for key, item in value.items()
        for warning in (
            item
            if key in ("warnings", "importWarnings") and isinstance(item, list)
            else json_warnings(item)
        )
    ]


class CliEngine(Engine):
    PRODUCT: str
    MIN_VERSION = "0.0.0"
    kind = "cli"

    @property
    def name(self) -> str:
        return self.PRODUCT

    def binary(self) -> Path | None:
        override = os.environ.get(f"MCRUFT_{self.PRODUCT.upper()}_CLI")
        if override:
            path = Path(override).expanduser().absolute()
        else:
            package = f"mcruft_{self.PRODUCT}_bin"
            try:
                path = Path(importlib.import_module(package).BIN).absolute()
            except ModuleNotFoundError as exc:
                if exc.name != package:
                    raise
                found = shutil.which(f"{self.PRODUCT}-cli")
                path = Path(found).absolute() if found else None
        return path if path and path.is_file() and os.access(path, os.X_OK) else None

    def available(self) -> bool:
        return self.binary() is not None

    def version(self) -> str | None:
        binary = self.binary()
        return parse_version(run_cli([binary, "--version"]).stdout) if binary else None

    def report(self, op: str, policy: Policy, outputs: list[Path] | None = None) -> Report:
        current = self.version()
        report = Report(op, policy, self.name, current, outputs or [])
        if current and tuple(map(int, re.match(r"\d+\.\d+\.\d+", current)[0].split("."))) < tuple(
            map(int, self.MIN_VERSION.split("."))
        ):
            report.warnings.append(f"{self.name} {current} is older than {self.MIN_VERSION}")
        return report

    def check_route(self, op: str, src: Path, dst: Path, policy: Policy) -> None:
        if op == "inspect" or not any(
            (c.op, c.src, c.dst, c.policy)
            == (op, src.suffix.lower()[1:], dst.suffix.lower()[1:], policy)
            for c in self.capabilities()
        ):
            raise UnsupportedRoute(f"{self.name}: {op} {src.suffix} -> {dst.suffix} ({policy})")

    def call(self, args: list[str | Path], report: Report | None = None) -> str:
        binary = self.binary()
        if binary is None:
            raise EngineUnavailable(f"Missing {self.PRODUCT}-cli")
        result = run_cli([binary, *args])
        if report is not None:
            for line in result.stdout.splitlines():
                try:
                    report.warnings.extend(json_warnings(json.loads(line)))
                except json.JSONDecodeError:
                    pass  # Some CLIs print human-readable progress instead of JSON.
            report.warnings.extend(
                line.removeprefix("warning: ")
                for line in result.stderr.splitlines()
                if line.startswith("warning: ")
            )
        return result.stdout

    def run(self, op: str, src: Path, dst: Path, *, policy: Policy, **opts) -> Report:
        raise UnsupportedRoute("implemented in Task 6")

    async def session(self, read_root: Path, write_root: Path, extra_args: list[str] | None = None):
        from ..mcp import McpSession

        binary = self.binary()
        if binary is None:
            raise EngineUnavailable(f"Missing {self.PRODUCT}-cli")
        return await McpSession().open(binary, read_root, write_root, extra_args)
