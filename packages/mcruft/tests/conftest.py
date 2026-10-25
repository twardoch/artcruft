# this_file: packages/mcruft/tests/conftest.py
from pathlib import Path

import pytest
from pypdf import PdfWriter


@pytest.fixture
def pdf(tmp_path: Path) -> Path:
    path = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(200, 300)
    writer.add_blank_page(400, 500).rotate(90)
    writer.write(path)
    return path


@pytest.fixture
def isolated(monkeypatch):
    from mcruft.engines import registry
    from mcruft.engines.lib import engine

    monkeypatch.setattr(registry, "entry_points", lambda **kw: [])
    monkeypatch.setattr(registry, "_registered", {})
    registry.register(engine)
