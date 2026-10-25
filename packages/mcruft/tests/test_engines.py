# this_file: packages/mcruft/tests/test_engines.py
import importlib.metadata
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import mcruft
import pytest
from mcruft import EngineFailed, UnsupportedRoute
from mcruft.engines import registry
from mcruft.engines.base import Capability, Engine
from mcruft.engines.cli import CliEngine, run_cli


class FakeEngine(Engine):
    def __init__(self, name, kind, verified=True, available=True):
        self.name, self.kind, self.verified, self.present = name, kind, verified, available

    def available(self):
        return self.present

    def capabilities(self):
        return [Capability("convert", "a", "b", "editable", "tested" if self.verified else None)]


def test_route_when_multiple_engines_then_verified_kind_order_and_pinning(monkeypatch):
    monkeypatch.setattr(registry, "entry_points", lambda **kwargs: [])
    monkeypatch.setattr(registry, "_registered", {})
    engines = [
        FakeEngine("unverified", "native", False),
        FakeEngine("mcp", "mcp"),
        FakeEngine("cli", "cli"),
        FakeEngine("lib", "lib"),
        FakeEngine("absent", "native", available=False),
        FakeEngine("native", "native"),
    ]
    for engine in engines:
        registry.register(engine)
    assert registry.route("convert", "a", "b", "editable")[0].name == "native"
    registry._registered.pop("native")
    assert registry.route("convert", "a", "b", "editable")[0].name == "lib"
    assert registry.route("convert", "a", "b", "editable", "cli")[0].name == "cli"
    with pytest.raises(UnsupportedRoute):
        registry.route("convert", "a", "b", "editable", "absent")
    with pytest.raises(UnsupportedRoute):
        registry.route("convert", "a", "b", "fidelity")


def test_discover_when_workspace_installed_then_finds_all_engines():
    names = {ep.name for ep in importlib.metadata.entry_points(group="mcruft.engines")}
    expected = {"lib", "vectorcraft", "deckcraft", "photocraft", "pdfcraft", "designcraft"}
    assert names == expected
    assert {engine.name for engine in registry.discover()} == expected


def test_engines_when_product_binaries_missing_then_reports_availability(monkeypatch, tmp_path):
    for product in ("vectorcraft", "deckcraft", "photocraft", "pdfcraft", "designcraft"):
        monkeypatch.setenv(f"MCRUFT_{product.upper()}_CLI", str(tmp_path / "missing"))
    info = {engine.name: engine for engine in mcruft.engines()}
    assert info["lib"].available
    assert all(not engine.available for name, engine in info.items() if name != "lib")


def test_binary_when_env_then_overrides_bundle_and_path(tmp_path, monkeypatch):
    binary = tmp_path / "fake-cli"
    binary.write_text('#!/bin/sh\necho "fake 0.1.0"\n')
    binary.chmod(0o755)
    engine = CliEngine()
    engine.PRODUCT, engine.MIN_VERSION = "fake", "0.2.0"
    monkeypatch.setenv("MCRUFT_FAKE_CLI", str(binary))
    assert engine.binary() == binary
    assert engine.available()
    assert engine.report("convert", "editable").warnings == ["fake 0.1.0 is older than 0.2.0"]
    monkeypatch.delenv("MCRUFT_FAKE_CLI")
    monkeypatch.setattr(importlib, "import_module", lambda name: SimpleNamespace(BIN=binary))
    assert engine.binary() == binary
    monkeypatch.setenv("MCRUFT_FAKE_CLI", str(tmp_path / "missing"))
    assert not engine.available()


def test_run_cli_when_failure_then_includes_argv_and_stderr():
    with pytest.raises(EngineFailed, match="specific failure") as exc:
        run_cli(
            [sys.executable, "-c", 'import sys; sys.stderr.write("specific failure"); sys.exit(3)']
        )
    assert sys.executable in str(exc.value)


def test_run_cli_when_timeout_then_raises():
    with pytest.raises(EngineFailed):
        run_cli([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.01)


def test_run_cli_when_path_argument_then_makes_absolute(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **kw: calls.append(args))
    run_cli(["fake", Path("-document.pdf")])
    assert Path(calls[0][1]).is_absolute()
