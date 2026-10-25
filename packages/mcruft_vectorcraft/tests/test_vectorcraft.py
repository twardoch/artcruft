# this_file: packages/mcruft_vectorcraft/tests/test_vectorcraft.py
import pytest
from mcruft import UnsupportedRoute
from mcruft.engines.cli import run_cli
from mcruft_vectorcraft import engine
from PIL import Image
from pypdf import PdfReader, PdfWriter

pytestmark = pytest.mark.skipif(not engine.available(), reason="vectorcraft-cli not installed")


def test_unknown_route(tmp_path):
    with pytest.raises(UnsupportedRoute):
        engine.run("convert", tmp_path / "in.unknown", tmp_path / "out.unknown", policy="editable")


def test_declared_routes(tmp_path):
    svg = tmp_path / "input.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="96pt" height="48pt">'
        '<text x="3" y="24" font-family="Arial" font-size="12">Hello</text></svg>'
    )
    inputs = {"svg": svg}
    for ext in ("pdf", "vectorcraft", "ai", "eps"):
        inputs[ext] = tmp_path / f"input.{ext}"
        run_cli([engine.binary(), "convert", svg, inputs[ext]])
    exercised = set()
    for n, cap in enumerate(engine.capabilities()):
        src = inputs[cap.src]
        dst = tmp_path / f"route-{n}.{cap.dst}"
        if cap.op == "inspect":
            assert engine.inspect(src) == [(96, 48)]
        else:
            report = engine.run(cap.op, src, dst, policy=cap.policy, pages=[0], dpi=144)
            if cap.op == "export_pages" and cap.dst == "png":
                dst = dst.with_name(f"{dst.stem}-0000.png")
            assert report.outputs == [dst]
            assert dst.stat().st_size > 0
            if cap.dst == "pdf":
                assert len(PdfReader(dst).pages) == 1
                assert float(PdfReader(dst).pages[0].mediabox.width) == pytest.approx(96)
            if cap.dst == "png":
                with Image.open(dst) as image:
                    assert image.size == (192, 96)
                assert any(loss.kind == "raster" for loss in report.losses)
            if cap.dst == "psd":
                with Image.open(dst) as image:
                    assert image.size == (96, 48)
                assert any(loss.kind == "raster" for loss in report.losses)
            if cap.op == "outline_text":
                assert report.losses[0].detail == (
                    "re-imported via VectorCraft: links, annotations and forms may be dropped"
                )
                assert b"/FontFile" not in dst.read_bytes()
                if cap.dst == "svg":
                    assert "<text" not in dst.read_text()
            elif cap.dst == "svg":
                assert "<text" in dst.read_text()
        exercised.add((cap.op, cap.src, cap.dst, cap.policy))
    assert {
        (c.op, c.src, c.dst, c.policy) for c in engine.capabilities() if c.verified_with
    } <= exercised


def test_export_svg_png_page_contract(tmp_path):
    src = tmp_path / "input.svg"
    src.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="96pt" height="48pt"/>')
    report = engine.run(
        "export_pages", src, tmp_path / "page.png", policy="fidelity", pages=[0], dpi=72
    )
    assert report.outputs == [tmp_path / "page-0000.png"]
    with Image.open(report.outputs[0]) as image:
        assert image.size == (96, 48)


def test_page_order_duplicates_and_warnings(tmp_path):
    pdf = tmp_path / "input.pdf"
    writer = PdfWriter()
    writer.add_blank_page(96, 48)
    writer.add_blank_page(144, 72)
    writer.write(pdf)
    native = tmp_path / "input.vectorcraft"
    run_cli([engine.binary(), "convert", pdf, native])
    for pages, expected in (
        (None, [96, 144]),
        ([1], [144]),
        ([1, 0], [144, 96]),
        ([1, 0, 1], [144, 96, 144]),
    ):
        dst = tmp_path / "selected.pdf"
        report = engine.run("export_pages", native, dst, policy="editable", pages=pages)
        assert [float(p.mediabox.width) for p in PdfReader(dst).pages] == expected
        if pages == [1]:
            assert any("Preserve editing" in warning for warning in report.warnings)
    with pytest.raises((ValueError, IndexError)):
        engine.run("export_pages", native, tmp_path / "bad.pdf", policy="editable", pages=[-1])


def test_json_warnings_and_cli_failure(tmp_path, monkeypatch):
    from mcruft import EngineFailed

    binary = tmp_path / "fake-cli"
    binary.write_text(
        '#!/bin/sh\nif [ "$1" = "--version" ]; then echo "0.16.0"; exit; fi\n'
        'echo \'{"warnings":["first"],"result":{"warnings":["second"]}}\'\n'
        'echo \'{"warnings":["third"]}\'\n'
    )
    binary.chmod(0o755)
    monkeypatch.setenv("MCRUFT_VECTORCRAFT_CLI", str(binary))
    report = engine.run(
        "outline_text", tmp_path / "in.svg", tmp_path / "out.svg", policy="fidelity"
    )
    assert report.warnings == ["first", "second", "third"]
    binary.write_text('#!/bin/sh\necho "broken CLI" >&2\nexit 1\n')
    with pytest.raises(EngineFailed, match="broken CLI"):
        engine.run("convert", tmp_path / "in.svg", tmp_path / "out.pdf", policy="editable")
