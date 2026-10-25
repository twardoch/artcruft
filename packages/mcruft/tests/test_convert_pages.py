# this_file: packages/mcruft/tests/test_convert_pages.py
import mcruft
import pytest
from mcruft.engines import registry
from PIL import Image
from pypdf import PdfWriter

from .fakes import Fake


@pytest.mark.parametrize("count", [1, 2])
def test_convert_falls_back_to_all_pages_with_correct_names(isolated, tmp_path, count):
    fake = Fake(("export_pages", "pdf", "png", "fidelity"))

    def export(op, src, dst, *, policy, **opts):
        fake.calls.append((op, policy, opts["pages"]))
        outputs = []
        for index in opts["pages"]:
            path = dst.with_name(f"{dst.stem}-{index:04d}.png")
            Image.new("RGB", (10 + index, 20)).save(path)
            outputs.append(path)
        return mcruft.Report(
            op,
            policy,
            "fake",
            outputs=outputs,
            losses=[mcruft.Loss("raster", "rendered")],
            warnings=["kept warning"],
        )

    fake.run = export
    registry.register(fake)
    source = tmp_path / "source.pdf"
    writer = PdfWriter()
    for _ in range(count):
        writer.add_blank_page(100, 200)
    writer.write(source)
    target = tmp_path / "out.png"
    report = mcruft.convert_fidelity(source, target)
    expected = [target] if count == 1 else [tmp_path / f"out-{i:04d}.png" for i in range(count)]
    assert report.op == "convert" and report.outputs == expected
    assert fake.calls == [("export_pages", "fidelity", list(range(count)))]
    assert report.warnings == ["kept warning"] and report.losses[0].detail == "rendered"
    assert all(path.is_file() for path in expected)


def test_convert_png_rejects_editable_even_if_export_declared(isolated, pdf, tmp_path):
    fake = Fake(("export_pages", "pdf", "png", "editable"))
    registry.register(fake)
    with pytest.raises(mcruft.UnsupportedRoute, match="raster targets accept only fidelity"):
        mcruft.convert_editable(pdf, tmp_path / "out.png")
    assert not fake.calls


def test_photocraft_matching_fidelity_routes():
    from mcruft_photocraft import engine

    declared = {(cap.src, cap.dst, cap.policy) for cap in engine.capabilities()}
    for src, dst in (("png", "psd"), ("jpg", "psd"), ("psd", "pcraft")):
        assert (src, dst, "fidelity") in declared
