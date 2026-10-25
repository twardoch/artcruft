# this_file: packages/mcruft_designcraft/tests/test_designcraft.py
import pytest
from mcruft import UnsupportedRoute
from mcruft.engines.cli import run_cli
from mcruft_designcraft import engine
from PIL import Image
from pptx import Presentation
from pypdf import PdfReader

pytestmark = pytest.mark.skipif(not engine.available(), reason="designcraft-cli not installed")


def test_unknown_route(tmp_path):
    with pytest.raises(UnsupportedRoute):
        engine.run("convert", tmp_path / "in.unknown", tmp_path / "out.unknown", policy="editable")


def test_declared_routes_and_page_base(tmp_path):
    idml = tmp_path / "in.idml"
    run_cli([engine.binary(), "run", "--sample", "--export", idml])
    original = idml.read_bytes()
    native = tmp_path / "in.designcraft"
    run_cli([engine.binary(), "run", "--in", idml, "--export", native])
    inputs = {"idml": idml, "designcraft": native}
    exercised = set()
    for n, cap in enumerate(engine.capabilities()):
        dst = tmp_path / f"route-{n}.{cap.dst}"
        if cap.op == "inspect":
            assert engine.inspect(inputs[cap.src]) == [(612, 792)] * 4
        else:
            report = engine.run(
                cap.op, inputs[cap.src], dst, policy=cap.policy, pages=[2, 0, 2], dpi=36
            )
            assert all(p.stat().st_size > 0 for p in report.outputs)
            if cap.dst == "pdf":
                pdf = PdfReader(dst)
                assert len(pdf.pages) == (3 if cap.op == "export_pages" else 4)
                if cap.op == "export_pages":
                    assert "SPRING ISSUE  ·  3" in pdf.pages[0].extract_text()
                    assert pdf.pages[0].extract_text() == pdf.pages[2].extract_text()
                    assert pdf.pages[0].extract_text() != pdf.pages[1].extract_text()
            if cap.dst == "pptx":
                assert len(Presentation(dst).slides) == 4
            if cap.dst in ("idml", "designcraft"):
                assert engine.inspect(dst) == [(612, 792)] * 4
            if cap.dst == "png":
                assert report.outputs == [
                    dst.with_name(f"{dst.stem}-{i:04d}.png") for i in [2, 0, 2]
                ]
                for path in report.outputs:
                    with Image.open(path) as image:
                        assert image.size == (306, 396)
                assert report.outputs[0].read_bytes() != report.outputs[1].read_bytes()
        exercised.add((cap.op, cap.src, cap.dst, cap.policy))
    assert {
        (c.op, c.src, c.dst, c.policy) for c in engine.capabilities() if c.verified_with
    } <= exercised
    # Compare the CLI's all-pages render with individual pages: --page is 0-based.
    all_dir = tmp_path / "reference"
    run_cli(
        [
            engine.binary(),
            "run",
            "--in",
            idml,
            "--cmd",
            'layout.documentSetup={"bleed":0}',
            "--scale",
            "0.5",
            "--all-pages",
            all_dir,
        ]
    )
    report = engine.run("export_pages", idml, tmp_path / "all.png", policy="fidelity", dpi=36)
    assert len(report.outputs) == 4
    for i, path in enumerate(report.outputs):
        assert path.read_bytes() == (all_dir / f"page-{i + 1:03d}.png").read_bytes()
    pdf_report = engine.run("export_pages", native, tmp_path / "all.pdf", policy="editable")
    assert len(PdfReader(pdf_report.outputs[0]).pages) == 4
    assert idml.read_bytes() == original, "Removing export bleed must not modify the source"
