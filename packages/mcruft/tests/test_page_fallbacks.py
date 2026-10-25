# this_file: packages/mcruft/tests/test_page_fallbacks.py
import mcruft
import pytest
from mcruft.engines import registry
from PIL import Image
from pypdf import PdfReader, PdfWriter

from .fakes import Fake


@pytest.mark.parametrize(
    "operation, policy",
    [
        ("export_pages", "fidelity"),
        ("convert", "editable"),
        ("convert", "fidelity"),
    ],
)
def test_pdf_page_route_fallbacks(isolated, tmp_path, operation, policy):
    fake = Fake(("inspect", "one", "one", "editable"), (operation, "one", "pdf", policy))
    fake.inspect = lambda path: [(100, 200)]
    original_run = fake.run

    def selected(op, src, dst, **opts):
        report = original_run(op, src, dst, **opts)
        if op == "export_pages":
            writer = PdfWriter()
            for index in opts["pages"]:
                writer.add_page(PdfReader(src).pages[index])
            writer.write(dst)
        return report

    fake.run = selected
    registry.register(fake)
    source = tmp_path / "source.one"
    writer = PdfWriter()
    writer.add_blank_page(100, 200)
    writer.write(source)
    doc = mcruft.open(source)
    target = tmp_path / "result.pdf"
    doc.export(target, policy=policy, fonts="embed", pages=[0, 0])
    assert len(PdfReader(target).pages) == 2
    assert [(c[0], c[3]) for c in fake.calls] == [(operation, policy)]


@pytest.mark.parametrize("fmt", ["png", "jpg", "jpeg", "psd", "pcraft"])
def test_raster_pdf_uses_fidelity_without_added_loss(isolated, tmp_path, fmt):
    fake = Fake(("inspect", fmt, fmt, "editable"), ("convert", fmt, "pdf", "fidelity"))
    fake.inspect = lambda path: [(100, 200)]
    run = fake.run

    def convert(*args, **kwargs):
        report = run(*args, **kwargs)
        report.losses.clear()
        return report

    fake.run = convert
    registry.register(fake)
    source = tmp_path / f"source.{fmt}"
    writer = PdfWriter()
    writer.add_blank_page(100, 200)
    writer.write(source)
    doc = mcruft.open(source)
    for policy in ("editable", "fidelity"):
        report = doc.export(tmp_path / f"{policy}.pdf", policy=policy, fonts="embed")
        assert report.losses == []
        assert fake.calls[-1][3] == "fidelity"


def test_png_page_render_respects_dpi(isolated, tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (40, 60), "red").save(source, dpi=(144, 144))
    doc = mcruft.open(source)
    target = tmp_path / "render.png"
    doc.pages[0].render(target, dpi=72)
    with Image.open(target) as image:
        assert image.size == (20, 30)


def test_raster_convert_both_policies(isolated, tmp_path):
    fake = Fake(("convert", "png", "pdf", "fidelity"))
    registry.register(fake)
    source = tmp_path / "image.png"
    Image.new("RGB", (20, 30)).save(source)
    for policy in ("editable", "fidelity"):
        report = mcruft.convert(source, tmp_path / f"{policy}.pdf", policy=policy)
        assert report.policy == policy and fake.calls[-1][3] == "fidelity"


@pytest.mark.parametrize("has_fidelity", [False, True])
def test_fidelity_page_export_route_order_then_outline(isolated, tmp_path, has_fidelity):
    caps = [
        ("inspect", "one", "one", "editable"),
        ("export_pages", "one", "pdf", "editable"),
        ("outline_text", "pdf", "pdf", "fidelity"),
    ]
    if has_fidelity:
        caps.append(("export_pages", "one", "pdf", "fidelity"))
    fake = Fake(*caps)
    fake.inspect = lambda path: [(100, 200)]
    registry.register(fake)
    source = tmp_path / "source.one"
    writer = PdfWriter()
    writer.add_blank_page(100, 200)
    writer.write(source)
    output = tmp_path / "outlined.pdf"
    report = mcruft.open(source).export(output, policy="fidelity", fonts="outline")
    expected = "fidelity" if has_fidelity else "editable"
    assert [(c[0], c[3]) for c in fake.calls] == [
        ("export_pages", expected),
        ("outline_text", "fidelity"),
    ]
    assert len(PdfReader(output).pages) == 1
    assert report.outputs == [output] and report.policy == "fidelity"
