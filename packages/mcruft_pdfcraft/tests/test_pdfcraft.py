# this_file: packages/mcruft_pdfcraft/tests/test_pdfcraft.py
import pytest
from mcruft import UnsupportedRoute
from mcruft.engines.cli import run_cli
from mcruft_pdfcraft import engine
from mcruft_vectorcraft import engine as vector
from PIL import Image
from pypdf import PdfReader, PdfWriter

pytestmark = pytest.mark.skipif(not engine.available(), reason="pdfcraft-cli not installed")


def test_unknown_route(tmp_path):
    with pytest.raises(UnsupportedRoute):
        engine.run("convert", tmp_path / "in.unknown", tmp_path / "out.unknown", policy="editable")


def test_declared_routes(tmp_path):
    if not vector.available():
        pytest.skip("vectorcraft-cli needed to generate PDF fixture")
    svg = tmp_path / "in.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="96pt" height="48pt">'
        '<text x="3" y="24">Hello</text></svg>'
    )
    single = tmp_path / "one.pdf"
    run_cli([vector.binary(), "convert", svg, single])
    src = tmp_path / "in.pdf"
    writer = PdfWriter()
    writer.append(single)
    writer.add_blank_page(144, 72)
    writer.write(src)
    exercised = set()
    for cap in engine.capabilities():
        for indexes in (None, [1], [1, 0, 1]):
            dst = tmp_path / f"out.{cap.dst}"
            report = engine.run(cap.op, src, dst, policy=cap.policy, pages=indexes, dpi=144)
            chosen = [0, 1] if indexes is None else indexes
            if cap.dst == "pdf":
                assert report.outputs == [dst]
                assert [float(p.mediabox.width) for p in PdfReader(dst).pages] == [
                    (96, 144)[i] for i in chosen
                ]
            else:
                assert report.outputs == [dst.with_name(f"out-{i:04d}.png") for i in chosen]
                for path, i in zip(report.outputs, chosen):
                    with Image.open(path) as image:
                        assert image.size == ((192, 96), (288, 144))[i]
            exercised.add((cap.op, cap.src, cap.dst, cap.policy))
    assert {
        (c.op, c.src, c.dst, c.policy) for c in engine.capabilities() if c.verified_with
    } <= exercised
    for pages in ([], [-1], [2]):
        with pytest.raises((ValueError, IndexError)):
            engine.run("export_pages", src, tmp_path / "bad.pdf", policy="editable", pages=pages)
    for dpi in (0, -1, float("nan")):
        with pytest.raises(ValueError):
            engine.run("export_pages", src, tmp_path / "bad.png", policy="fidelity", dpi=dpi)
