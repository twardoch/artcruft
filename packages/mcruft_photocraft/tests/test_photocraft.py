# this_file: packages/mcruft_photocraft/tests/test_photocraft.py
import mcruft
import pytest
from mcruft import UnsupportedRoute
from mcruft.engines.cli import run_cli
from mcruft_photocraft import engine
from PIL import Image
from pypdf import PdfReader

pytestmark = pytest.mark.skipif(not engine.available(), reason="photocraft-cli not installed")


def test_unknown_route(tmp_path):
    with pytest.raises(UnsupportedRoute):
        engine.run("convert", tmp_path / "in.unknown", tmp_path / "out.unknown", policy="editable")


def test_declared_routes(tmp_path):
    inputs = {}
    for ext in ("png", "jpg"):
        inputs[ext] = tmp_path / f"in.{ext}"
        Image.new("RGB", (96, 48), "red").save(inputs[ext], dpi=(144, 144))
    for ext, source in (("psd", "png"), ("pcraft", "psd")):
        inputs[ext] = tmp_path / f"in.{ext}"
        run_cli([engine.binary(), "convert", inputs[source], inputs[ext]])
    exercised = set()
    for n, cap in enumerate(engine.capabilities()):
        dst = tmp_path / f"route-{n}.{cap.dst}"
        if cap.op == "inspect":
            assert engine.inspect(inputs[cap.src])[0] == pytest.approx((48, 24), abs=0.01)
        else:
            report = engine.run(cap.op, inputs[cap.src], dst, policy=cap.policy)
            assert report.outputs == [dst] and dst.stat().st_size > 0
            if cap.dst == "pdf":
                assert len(PdfReader(dst).pages) == 1
            if cap.dst in ("png", "psd"):
                with Image.open(dst) as image:
                    assert image.size == (96, 48)
            if cap.dst == "pcraft":
                assert engine.inspect(dst)[0] == pytest.approx((48, 24), abs=0.01)
        exercised.add((cap.op, cap.src, cap.dst, cap.policy))
    assert {
        (c.op, c.src, c.dst, c.policy) for c in engine.capabilities() if c.verified_with
    } <= exercised


@pytest.mark.parametrize("fmt", ["psd", "pcraft"])
def test_layered_page_pdf_export_and_previews(tmp_path, fmt):
    from mcruft_vectorcraft import engine as vectorcraft

    if not vectorcraft.available():
        pytest.skip("vectorcraft-cli required for fidelity PDF outlining")
    png = tmp_path / "input.png"
    Image.new("RGB", (96, 48), "red").save(png)
    psd = tmp_path / "input.psd"
    run_cli([engine.binary(), "convert", png, psd])
    source = psd
    if fmt == "pcraft":
        source = tmp_path / "input.pcraft"
        run_cli([engine.binary(), "convert", psd, source])
    doc = mcruft.open(source)
    for policy in ("editable", "fidelity"):
        target = tmp_path / f"{policy}.pdf"
        report = doc.export(target, policy=policy)
        assert len(PdfReader(target).pages) == 1
        assert b"/FontFile" not in target.read_bytes(), (
            "Flattened image pages must not depend on fonts"
        )
        assert any(
            (loss.kind, loss.detail) == ("effects", "layers flattened") for loss in report.losses
        )
    report = engine.run("convert", source, tmp_path / "flat.png", policy="fidelity")
    assert any(
        (loss.kind, loss.detail) == ("effects", "layers flattened") for loss in report.losses
    )
    doc.save(tmp_path / "doc.mcruft", previews=True)
    loaded = mcruft.load(doc.path)
    assert len(PdfReader(loaded.assets[loaded.pages[0].preview].path).pages) == 1
