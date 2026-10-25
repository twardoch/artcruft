# this_file: packages/mcruft/tests/test_safety.py
import mcruft
import pytest
from mcruft.engines import registry

from .fakes import Fake


@pytest.mark.parametrize("saved", [False, True])
@pytest.mark.parametrize("operation", ["export", "render", "numbered"])
def test_asset_target_is_refused_before_writes(isolated, pdf, tmp_path, saved, operation):
    doc = mcruft.open(pdf)
    if saved:
        doc.save(tmp_path / "doc.mcruft")
    source = doc.assets[doc.pages[0].source["asset"]].path
    if operation == "numbered":
        from PIL import Image

        source = tmp_path / "thumb-0000.png"
        Image.new("RGB", (20, 30)).save(source)
        added = doc.add_file(source)
        source = doc.assets[added[0].source["asset"]].path
    before = source.read_bytes()
    with pytest.raises(mcruft.PackageError, match="asset"):
        if operation == "render":
            registry.register(Fake(("export_pages", "pdf", "png", "fidelity")))
            doc.pages[0].render(source)
        elif operation == "numbered":
            registry.register(Fake(("export_pages", "pdf", "png", "fidelity")))
            doc.export(source.with_name("thumb.png"), policy="fidelity", pages=[0])
        else:
            doc.export(source, policy="editable", pages=[1])
    assert source.read_bytes() == before, "Refused exports must preserve asset bytes"


@pytest.mark.parametrize("existing", [False, True])
def test_failed_outline_preserves_target(isolated, pdf, tmp_path, existing):
    fake = Fake(("outline_text", "pdf", "pdf", "fidelity"))

    def fail(*args, **kwargs):
        raise mcruft.EngineFailed("outline failed")

    fake.run = fail
    registry.register(fake)
    target = tmp_path / "out.pdf"
    if existing:
        target.write_bytes(b"previous output")
    with pytest.raises(mcruft.EngineFailed, match="outline failed"):
        mcruft.open(pdf).export(target, policy="fidelity")
    assert target.read_bytes() == b"previous output" if existing else not target.exists()


def test_render_and_png_export_preserve_siblings(isolated, pdf, tmp_path):
    registry.register(Fake(("export_pages", "pdf", "png", "fidelity")))
    doc = mcruft.open(pdf)
    sibling = tmp_path / "thumb-0000.png"
    sibling.write_bytes(b"unrelated render sibling")
    doc.pages[0].render(tmp_path / "thumb.png")
    assert sibling.read_bytes() == b"unrelated render sibling"
    sibling = tmp_path / "selected-0001.png"
    sibling.write_bytes(b"unrelated source-index sibling")
    report = doc.export(tmp_path / "selected.png", policy="fidelity", pages=[1])
    assert report.outputs == [tmp_path / "selected-0000.png"]
    assert sibling.read_bytes() == b"unrelated source-index sibling"


@pytest.mark.parametrize("alias", [False, True])
def test_convert_refuses_same_resolved_path(isolated, pdf, tmp_path, alias):
    registry.register(Fake(("outline_text", "pdf", "pdf", "fidelity")))
    target = tmp_path / "alias.pdf" if alias else pdf
    if alias:
        target.symlink_to(pdf)
    before = pdf.read_bytes()
    with pytest.raises(ValueError, match="same"):
        mcruft.convert_fidelity(pdf, target)
    assert pdf.read_bytes() == before


@pytest.mark.parametrize("operation", ["export", "render", "convert"])
def test_missing_parent_has_package_error(isolated, pdf, tmp_path, operation):
    registry.register(Fake(("convert", "pdf", "svg", "editable")))
    target = tmp_path / "missing" / ("out.svg" if operation == "convert" else "out.pdf")
    doc = mcruft.open(pdf)
    with pytest.raises(mcruft.PackageError, match="parent.*missing"):
        if operation == "convert":
            mcruft.convert_editable(pdf, target)
        elif operation == "render":
            doc.pages[0].render(target)
        else:
            doc.export(target, policy="editable")
