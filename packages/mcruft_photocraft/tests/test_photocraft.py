# this_file: packages/mcruft_photocraft/tests/test_photocraft.py
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
