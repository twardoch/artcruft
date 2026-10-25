# this_file: packages/mcruft/tests/test_editing.py
import mcruft
import pytest
from mcruft.engines import registry
from pypdf import PdfReader

from .fakes import Fake


@pytest.mark.parametrize("saved", [False, True])
def test_edit_in_changed_unchanged_exception(isolated, pdf, tmp_path, saved):
    doc = mcruft.open(pdf)
    if saved:
        doc.save(tmp_path / "doc.mcruft", previews=True)
    page = doc.pages[1]
    source, preview, assets = page.source.copy(), page.preview, set(doc.assets)
    with page.edit_in("pdfcraft") as path:
        assert len(PdfReader(path).pages) == 2
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
    assert page.source["index"] == 1 and page.preview is None
    doc.save(tmp_path / "edited.mcruft")
    assert mcruft.load(doc.path).pages[1].source == page.source


@pytest.mark.parametrize(
    "engine, suffix",
    [
        ("vectorcraft", ".pdf"),
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
