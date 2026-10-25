# this_file: packages/mcruft_pdfcraft/tests/test_native.py
from types import SimpleNamespace

import mcruft
import pytest
from mcruft.engines import registry
from mcruft.engines.lib import engine as lib
from pypdf import PdfReader, PdfWriter


def test_native_unavailable_when_import_fails(monkeypatch, tmp_path):
    from mcruft_pdfcraft import native

    def missing(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(native, "import_module", missing)
    assert not native.engine.available()
    with pytest.raises(mcruft.EngineUnavailable):
        native.engine.run(
            "extract_pages", tmp_path / "in.pdf", tmp_path / "out.pdf", policy="editable"
        )


def test_native_signatures_and_routing_preference(monkeypatch, tmp_path):
    from mcruft_pdfcraft import native

    calls = []

    def page_count(path):
        assert isinstance(path, str)
        calls.append(("page_count", path))
        return len(PdfReader(path).pages)

    def extract(path, pages, out):
        calls.append(("extract", path, pages, out))
        writer = PdfWriter()
        for index in pages:
            writer.add_page(PdfReader(path).pages[index])
        writer.write(out)

    def combine(paths, out):
        calls.append(("combine", paths, out))
        writer = PdfWriter()
        for path in paths:
            writer.append(path)
        writer.write(out)

    module = SimpleNamespace(page_count=page_count, extract=extract, combine=combine)
    monkeypatch.setattr(native, "import_module", lambda name: module)
    monkeypatch.setattr(registry, "entry_points", lambda **kw: [])
    monkeypatch.setattr(registry, "_registered", {})
    registry.register(lib)
    registry.register(native.engine)
    source = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(100, 200)
    writer.add_blank_page(300, 400)
    writer.write(source)
    assert native.engine.available()
    for policy in ("editable", "fidelity"):
        engine, _ = registry.route("extract_pages", "pdf", "pdf", policy)
        assert engine.name == "pdfcraft-native" and engine.kind == "native"
        output = tmp_path / f"{policy}.pdf"
        report = engine.run("extract_pages", source, output, policy=policy, pages=[1, 0, 1])
        assert report.outputs == [output]
        assert [float(p.mediabox.width) for p in PdfReader(output).pages] == [300, 100, 300]
        combined = tmp_path / f"combined-{policy}.pdf"
        engine.run("combine", source, combined, policy=policy, paths=[source, output])
        assert len(PdfReader(combined).pages) == 5
    report = mcruft.open(source).export(tmp_path / "document.pdf", policy="editable", pages=[1, 0])
    assert report.engine == "pdfcraft-native+pdfcraft-native", "Core must not pin PDF work to lib"
    assert any(call[0] == "page_count" for call in calls)
    assert all(isinstance(call[-1], str) for call in calls if call[0] in ("extract", "combine"))
