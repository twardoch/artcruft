# this_file: packages/mcruft/tests/test_page_owner.py
import gc
from copy import deepcopy

import mcruft
from mcruft.ops import owner
from PIL import Image


def test_page_keeps_temporary_document_alive(isolated, tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (20, 30), "red").save(source)
    pages = mcruft.open(source).pages
    gc.collect()
    for page in pages:
        assert page.render(tmp_path / "render.png", dpi=72).outputs == [tmp_path / "render.png"]
        with page.edit_in("photocraft") as working:
            assert working.read_bytes() == source.read_bytes()
    assert not working.exists()


def test_page_owners_after_copy_split_merge(isolated, pdf):
    original = mcruft.open(pdf)
    copied = deepcopy(original)
    parts = original.split()
    merged = mcruft.merge(parts)
    for doc in [original, copied, *parts, merged]:
        assert all(owner(page) is doc for page in doc.pages)
