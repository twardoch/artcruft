# this_file: packages/mcruft/tests/test_adapter_fixes.py
import mcruft
import pytest
from mcruft.engines import registry
from mcruft_deckcraft import engine as deckcraft
from mcruft_photocraft import engine as photocraft

from .fakes import Fake


def test_build_deck_requires_images(tmp_path, monkeypatch):
    monkeypatch.setattr(deckcraft, "report", lambda op, policy, outputs: mcruft.Report(op, policy))
    with pytest.raises(ValueError, match="at least one image"):
        deckcraft.run("build_deck", tmp_path / "in.png", tmp_path / "out.pptx", policy="fidelity")


def test_jpeg_is_jpg_for_router_and_adapter(isolated, tmp_path):
    fake = Fake(("convert", "jpg", "psd", "editable"))
    registry.register(fake)
    src, dst = tmp_path / "source.jpeg", tmp_path / "out.psd"
    src.write_bytes(b"image")
    assert mcruft.convert_editable(src, dst).outputs == [dst]
    photocraft.check_route("convert", src, dst, "editable")
