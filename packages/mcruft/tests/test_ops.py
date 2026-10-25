# this_file: packages/mcruft/tests/test_ops.py

import mcruft
import pytest
from mcruft.engines import registry
from mcruft.engines.lib import engine as lib
from mcruft.package import digest
from PIL import Image
from pypdf import PdfReader, PdfWriter


class Fake(mcruft.Engine):
    name, kind = "fake", "native"

    def __init__(self, *caps):
        self.caps, self.calls = caps, []

    def available(self):
        return True

    def version(self):
        return "1"

    def capabilities(self):
        return [mcruft.Capability(*c, "tested") for c in self.caps]

    def run(self, op, src, dst, *, policy, **opts):
        self.calls.append((op, src, dst, policy, opts))
        outputs = [dst]
        if dst.suffix == ".png":
            outputs = [dst.with_name(f"{dst.stem}-{opts['pages'][0]:04d}.png")]
            Image.new("RGB", (20, 30)).save(outputs[0])
        else:
            dst.write_bytes(src.read_bytes())
        return mcruft.Report(op, policy, self.name, "1", outputs, [mcruft.Loss("layout", op)], [op])


@pytest.fixture
def isolated(monkeypatch):
    monkeypatch.setattr(registry, "entry_points", lambda **kw: [])
    monkeypatch.setattr(registry, "_registered", {})
    registry.register(lib)


def test_convert_direct_composite_and_errors(isolated, tmp_path):
    fake = Fake(("convert", "a", "pdf", "editable"), ("outline_text", "pdf", "pdf", "fidelity"))
    registry.register(fake)
    src, dst = tmp_path / "in.a", tmp_path / "out.pdf"
    src.write_bytes(b"content")
    assert mcruft.convert_editable(src, dst).engine == "fake"
    report = mcruft.convert_fidelity(src, dst)
    assert report.outputs == [dst]
    assert report.engine == "fake+fake"
    assert report.warnings == ["convert", "outline_text"]
    assert len(report.losses) == 2


def test_convert_validation_and_unsupported(isolated, tmp_path):
    with pytest.raises(ValueError):
        mcruft.convert("a.pdf", "b.pdf", policy="bad")
    with pytest.raises(TypeError):
        mcruft.convert("a.pdf", "b.pdf")
    with pytest.raises(mcruft.UnsupportedRoute, match="a.*b.*fidelity.*editable"):
        registry.register(Fake(("convert", "a", "b", "editable")))
        mcruft.convert("a.a", "b.b", policy="fidelity")


def test_export_groups_selected_pdf_pages(isolated, pdf, tmp_path, monkeypatch):
    second = tmp_path / "second.pdf"
    writer = PdfWriter()
    writer.add_blank_page(600, 700)
    writer.write(second)
    doc = mcruft.open(pdf)
    doc.add_file(second)
    calls = []
    original = lib.run

    def record(*args, **kwargs):
        calls.append((args[0], kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(lib, "run", record)
    dst = tmp_path / "out.pdf"
    report = doc.export(dst, policy="editable", pages=[1, 0, 2, 0])
    assert report.op == "export"
    assert [float(p.mediabox.width) for p in PdfReader(dst).pages] == [400, 200, 600, 200]
    assert [opts["pages"] for op, opts in calls if op == "extract_pages"] == [[1, 0], [0], [0]]


def test_png_naming_render_svg_and_pptx_rules(isolated, pdf, tmp_path):
    fake = Fake(("export_pages", "pdf", "png", "fidelity"))
    registry.register(fake)
    doc = mcruft.open(pdf)
    report = doc.export(tmp_path / "out.png", policy="fidelity", pages=[1, 0, 1], dpi=72)
    assert [p.name for p in report.outputs] == ["out-0000.png", "out-0001.png", "out-0002.png"]
    assert all(p.is_file() for p in report.outputs)
    target = tmp_path / "exact.png"
    assert doc.pages[1].render(target).outputs == [target]
    assert target.is_file()
    with pytest.raises(mcruft.UnsupportedRoute, match="one page"):
        doc.export(tmp_path / "out.svg", policy="editable")
    with pytest.raises(mcruft.UnsupportedRoute, match="no verified pdf->editable-slide route"):
        doc.export(tmp_path / "out.pptx", policy="editable")
    with pytest.raises(mcruft.UnsupportedRoute):
        doc.export(tmp_path / "out.unknown", policy="editable")


def test_save_previews_and_refresh(isolated, pdf, tmp_path):
    doc = mcruft.open(pdf)
    doc.save(tmp_path / "doc.mcruft", previews=True)
    loaded = mcruft.load(doc.path)
    old = loaded.pages[0].preview
    for n, page in enumerate(loaded.pages):
        asset = loaded.assets[page.preview]
        assert asset.role == "preview" and asset.derived_from == page.source["asset"]
        assert asset.path.name == f"page-{n:04d}.pdf"
        assert asset.sha256 == digest(asset.path)
        assert len(PdfReader(asset.path).pages) == 1
        assert asset.via["op"] == "export_pages"
    loaded.save(previews=True)
    assert loaded.pages[0].preview == old
    source = loaded.assets[loaded.pages[0].source["asset"]]
    source.path.write_bytes(source.path.read_bytes() + b"\n")
    loaded.refresh()
    loaded.save(previews=True)
    assert old not in loaded.assets
    assert loaded.pages[0].preview != old


@pytest.mark.parametrize("saved", [False, True])
def test_edit_in_changed_unchanged_exception(isolated, pdf, tmp_path, saved):
    doc = mcruft.open(pdf)
    if saved:
        doc.save(tmp_path / "doc.mcruft", previews=True)
    page = doc.pages[1]
    source, preview, assets = page.source.copy(), page.preview, set(doc.assets)
    with page.edit_in("pdfcraft") as path:
        assert len(PdfReader(path).pages) == 1
        if saved:
            assert path.parent == doc.path / "derived"
    assert not path.exists()
    assert page.source == source and page.preview == preview and set(doc.assets) == assets
    with pytest.raises(RuntimeError), page.edit_in("pdfcraft") as failed:
        failed.write_bytes(b"changed")
        raise RuntimeError("abort")
    assert page.source == source and set(doc.assets) == assets
    with page.edit_in("pdfcraft") as changed:
        changed.write_bytes(changed.read_bytes() + b"\nchanged")
    asset = doc.assets[page.source["asset"]]
    assert asset.path == changed and changed.is_file()
    assert asset.role == "derived" and asset.derived_from == source["asset"]
    assert asset.via == {"engine": "pdfcraft", "op": "edit_in"}
    assert page.source["index"] == 0 and page.preview is None
    doc.save(tmp_path / "edited.mcruft")
    assert mcruft.load(doc.path).pages[1].source == page.source


def test_convert_direct_fidelity_and_svg_via_pdf(isolated, tmp_path):
    fake = Fake(
        ("convert", "a", "pdf", "editable"),
        ("convert", "a", "png", "fidelity"),
        ("outline_text", "pdf", "svg", "fidelity"),
    )
    registry.register(fake)
    src = tmp_path / "in.a"
    src.write_bytes(b"content")
    report = mcruft.convert_fidelity(src, tmp_path / "out.svg")
    assert report.engine == "fake+fake" and len(report.losses) == 2
    assert [c[0] for c in fake.calls] == ["convert", "outline_text"]
    # A direct fidelity route must win over any composite route.
    fake.caps += (("convert", "a", "svg", "fidelity"),)
    assert mcruft.convert_fidelity(src, tmp_path / "direct.svg").engine == "fake"


def test_svg_single_page_and_fonts_override(isolated, pdf, tmp_path):
    fake = Fake(("convert", "pdf", "svg", "editable"), ("outline_text", "pdf", "pdf", "fidelity"))
    registry.register(fake)
    doc = mcruft.open(pdf)
    report = doc.export(tmp_path / "one.svg", policy="editable", pages=[1])
    assert len(PdfReader(report.outputs[0]).pages) == 1
    fake.calls.clear()
    doc.export(tmp_path / "embedded.pdf", policy="fidelity", fonts="embed")
    assert not fake.calls
    doc.export(tmp_path / "outlined.pdf", policy="editable", fonts="outline")
    assert fake.calls[0][0] == "outline_text"


def test_previews_reorder_and_missing_file(isolated, pdf, tmp_path):
    doc = mcruft.open(pdf)
    doc.save(tmp_path / "doc.mcruft", previews=True)
    doc.move_page(0, 1)
    doc.save(previews=True)
    doc = mcruft.load(doc.path)
    for n, page in enumerate(doc.pages):
        asset = doc.assets[page.preview]
        assert asset.path.name == f"page-{n:04d}.pdf"
        assert lib.inspect(asset.path) == [page.size]
        assert digest(asset.path) == asset.sha256
    old = doc.pages[0].preview
    doc.assets[old].path.unlink()
    doc.save(previews=True)
    assert old not in doc.assets


@pytest.mark.parametrize(
    "pages, exception", [([], ValueError), ([-1], IndexError), ([3], IndexError)]
)
def test_invalid_page_selections(isolated, pdf, tmp_path, pages, exception):
    with pytest.raises(exception):
        mcruft.open(pdf).export(tmp_path / "out.pdf", policy="editable", pages=pages)


def test_page_ownership_survives_split_merge_load(isolated, pdf, tmp_path):
    registry.register(Fake(("export_pages", "pdf", "png", "fidelity")))
    doc = mcruft.open(pdf)
    split = doc.split()
    merged = mcruft.merge(split)
    merged.save(tmp_path / "doc.mcruft")
    loaded = mcruft.load(merged.path)
    for n, candidate in enumerate([*split, merged, loaded]):
        target = tmp_path / f"render-{n}.png"
        assert candidate.pages[0].render(target).outputs == [target]


@pytest.mark.parametrize("name", ["absent", "unknown"])
def test_pin_unavailable_engine(isolated, name):
    fake = Fake()
    fake.name = "absent"
    fake.available = lambda: False
    registry.register(fake)
    with pytest.raises(mcruft.EngineUnavailable, match=name):
        registry.route("convert", "pdf", "svg", "editable", engine=name)


@pytest.mark.parametrize(
    "engine, suffix",
    [
        ("photocraft", ".psd"),
        ("vectorcraft", ".vectorcraft"),
        ("deckcraft", ".pptx"),
        ("pdfcraft", ".pdf"),
    ],
)
def test_edit_in_target_formats(isolated, pdf, tmp_path, engine, suffix):
    registry.register(
        Fake(
            ("convert", "pdf", "psd", "fidelity"),
            ("convert", "pdf", "svg", "editable"),
            ("convert", "svg", "vectorcraft", "editable"),
            ("export_pages", "pdf", "png", "fidelity"),
            ("build_deck", "png", "pptx", "fidelity"),
        )
    )
    doc = mcruft.open(pdf)
    doc.save(tmp_path / "doc.mcruft")
    with doc.pages[0].edit_in(engine) as path:
        assert path.suffix == suffix and path.is_file()
        path.write_bytes(path.read_bytes() + b"changed")
    assert doc.assets[doc.pages[0].source["asset"]].via["engine"] == engine


def test_invalid_export_options(isolated, pdf, tmp_path):
    doc = mcruft.open(pdf)
    with pytest.raises(ValueError, match="fonts"):
        doc.export(tmp_path / "out.pdf", policy="editable", fonts="")
    with pytest.raises(ValueError, match="DPI"):
        doc.pages[0].render(tmp_path / "out.png", dpi=0)
    with (
        pytest.raises(mcruft.UnsupportedRoute, match="Unknown edit engine"),
        doc.pages[0].edit_in("unknown"),
    ):
        pytest.fail("Unsupported editor must not yield")
