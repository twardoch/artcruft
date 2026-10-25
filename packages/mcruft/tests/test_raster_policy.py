# this_file: packages/mcruft/tests/test_raster_policy.py
import mcruft
import pytest
from PIL import Image


def test_png_export_rejects_editable_and_render_uses_fidelity(isolated, tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (20, 30)).save(source)
    doc = mcruft.open(source)
    with pytest.raises(mcruft.UnsupportedRoute, match="raster targets accept only fidelity"):
        doc.export(tmp_path / "out.png", policy="editable")
    assert not list(tmp_path.glob("out*.png")), "Refused policy must not write any output"
    report = doc.pages[0].render(tmp_path / "render.png", dpi=72)
    assert report.policy == "fidelity" and report.outputs == [tmp_path / "render.png"]
    with Image.open(report.outputs[0]) as image:
        assert image.size == (20, 30)


@pytest.mark.parametrize("fmt", ["png", "jpg"])
@pytest.mark.parametrize("has_profile", [False, True])
def test_raster_render_reports_dropped_icc_profile(isolated, tmp_path, fmt, has_profile):
    source = tmp_path / f"source.{fmt}"
    profile = b"ICC metadata fixture" if has_profile else None
    Image.new("RGB", (20, 30)).save(source, icc_profile=profile)
    doc = mcruft.open(source)
    report = doc.pages[0].render(tmp_path / "output.png", dpi=72)
    losses = [(loss.kind, loss.detail) for loss in report.losses]
    assert losses == ([("effects", "ICC profile not kept")] if has_profile else [])
    with Image.open(report.outputs[0]) as image:
        assert not image.info.get("icc_profile")
