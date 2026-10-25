# this_file: packages/mcruft/tests/test_libs.py
import importlib.util
from importlib.metadata import version

import pytest
from mcruft.engines import registry
from mcruft.engines.lib import engine
from PIL import Image
from pypdf import PdfWriter


@pytest.mark.parametrize("dpi", [72, 144])
def test_pdfium_export_when_pages_reordered_then_sizes_and_names_match(tmp_path, dpi, monkeypatch):
    pdfium = pytest.importorskip("pypdfium2")
    from mcruft.engines.libs_pdfium import PDFIUM_LOCK

    for cls, name in [
        (pdfium.PdfDocument, "__init__"),
        (pdfium.PdfDocument, "close"),
        (pdfium.PdfPage, "render"),
        (pdfium.PdfPage, "close"),
        (pdfium.PdfBitmap, "to_pil"),
        (pdfium.PdfBitmap, "close"),
    ]:
        original = getattr(cls, name)

        def locked_call(*args, _method=original, **kwargs):
            assert PDFIUM_LOCK.locked(), "PDFium calls and cleanup must hold the module lock"
            return _method(*args, **kwargs)

        monkeypatch.setattr(cls, name, locked_call)
    src = tmp_path / "input.pdf"
    with PdfWriter() as writer:
        writer.add_blank_page(200, 100)
        writer.add_blank_page(300, 400)
        writer.write(src)
    report = engine.run(
        "export_pages", src, tmp_path / "out.png", policy="fidelity", pages=[1, 0], dpi=dpi
    )
    assert [p.name for p in report.outputs] == ["out-0001.png", "out-0000.png"]
    for path, size in zip(report.outputs, [(300, 400), (200, 100)], strict=True):
        with Image.open(path) as image:
            assert image.size == tuple(v * dpi // 72 for v in size)
    assert any(loss.kind == "raster" for loss in report.losses)
    assert report.engine_version == version("pypdfium2")


@pytest.mark.parametrize("op", ["convert", "export_pages"])
@pytest.mark.parametrize("dpi", [96, 192])
def test_resvg_render_when_css_pixels_then_scales_at_96_dpi(tmp_path, op, dpi):
    pytest.importorskip("resvg_py")
    src, dst = tmp_path / "input.svg", tmp_path / "out.png"
    src.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100"/>')
    report = engine.run(op, src, dst, policy="fidelity", dpi=dpi)
    assert report.outputs == [dst if op == "convert" else tmp_path / "out-0000.png"]
    with Image.open(report.outputs[0]) as image:
        assert image.size == (200 * dpi // 96, 100 * dpi // 96)
    assert any(loss.kind == "raster" for loss in report.losses)
    assert any("system" in warning and "fonts" in warning for warning in report.warnings)
    assert report.engine_version == version("resvg-py")
    _, cap = registry.route(op, "svg", "png", "fidelity")
    assert cap.verified_with == f"lib resvg-py {version('resvg-py')}"


@pytest.mark.parametrize("dpi", [None, (144, 288)])
@pytest.mark.parametrize("policy", ["editable", "fidelity"])
def test_psd_inspect_when_resolution_present_or_absent_then_returns_points(tmp_path, dpi, policy):
    psd_tools = pytest.importorskip("psd_tools")
    from psd_tools.constants import Resource
    from psd_tools.psd.image_resources import ImageResource, ResoulutionInfo

    src = tmp_path / "input.psd"
    psd = psd_tools.PSDImage.new("RGB", (200, 100))
    if dpi:
        psd.image_resources[Resource.RESOLUTION_INFO] = ImageResource(
            key=Resource.RESOLUTION_INFO,
            data=ResoulutionInfo(horizontal=dpi[0] * 65536, vertical=dpi[1] * 65536),
        )
    else:
        psd.image_resources.pop(Resource.RESOLUTION_INFO, None)
    psd.save(src)
    backend, cap = registry.route("inspect", "psd", "psd", policy)
    assert backend is engine
    assert cap.verified_with == f"lib psd-tools {version('psd-tools')}"
    assert backend.inspect(src)[0] == pytest.approx((200, 100) if dpi is None else (100, 25))


def test_router_when_pdfium_installed_then_prefers_lib():
    pytest.importorskip("pypdfium2")
    backend, cap = registry.route("export_pages", "pdf", "png", "fidelity")
    assert backend is engine
    assert cap.verified_with == f"lib pypdfium2 {version('pypdfium2')}"


@pytest.mark.parametrize(
    "module,op,src,dst",
    [
        ("pypdfium2", "export_pages", "pdf", "png"),
        ("resvg_py", "convert", "svg", "png"),
        ("resvg_py", "export_pages", "svg", "png"),
        ("psd_tools", "inspect", "psd", "psd"),
    ],
)
def test_capability_when_optional_module_absent_then_disappears(monkeypatch, module, op, src, dst):
    find_spec = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: None if name == module else find_spec(name)
    )
    assert not any((c.op, c.src, c.dst) == (op, src, dst) for c in engine.capabilities())


@pytest.mark.parametrize("module,suffix", [("pypdfium2", "pdf"), ("resvg_py", "svg")])
@pytest.mark.parametrize(
    "opts,error",
    [
        ({"pages": []}, ValueError),
        ({"pages": [-1]}, IndexError),
        ({"pages": [99]}, IndexError),
        ({"dpi": 0}, ValueError),
        ({"dpi": float("nan")}, ValueError),
    ],
)
def test_library_render_when_options_invalid_then_refuses_before_writing(
    tmp_path, pdf, module, suffix, opts, error
):
    pytest.importorskip(module)
    src = pdf
    if suffix == "svg":
        src = tmp_path / "input.svg"
        src.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100"/>')
    with pytest.raises(error):
        engine.run("export_pages", src, tmp_path / "out.png", policy="fidelity", **opts)
    assert not list(tmp_path.glob("out*.png")), "Invalid options must not write outputs"
