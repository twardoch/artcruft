# this_file: packages/mcruft/tests/test_package.py
import json
from pathlib import Path

import mcruft
import pytest
from mcruft import Frame, PackageError, UnsupportedSchema


def test_save_when_round_trip_then_preserves_manifest(pdf, tmp_path):
    doc = mcruft.open(pdf)
    doc.pages[0].frames.append(Frame("f", "text", (0, 0, 10, 10)))
    doc.save(tmp_path / "talk.mcruft")
    loaded = mcruft.load(doc.path)
    assert loaded.pages[0].size == (200, 300)
    assert loaded.pages[0].frames == []
    assert loaded.assets.keys() == doc.assets.keys()
    assert mcruft.open(doc.path).meta == loaded.meta


def test_save_when_root_reached_via_symlink_then_reuses_assets(pdf, tmp_path):
    doc = mcruft.open(pdf)
    doc.save(tmp_path / "talk.mcruft")
    (tmp_path / "alias").symlink_to(tmp_path)
    loaded = mcruft.load(tmp_path / "alias" / "talk.mcruft")
    loaded.save(tmp_path / "talk.mcruft")
    assert [p.name for p in (tmp_path / "talk.mcruft" / "assets").iterdir()] == ["source.pdf"]


def test_add_file_when_name_clashes_then_copies_once(pdf, tmp_path):
    doc = mcruft.open(pdf)
    doc.save(tmp_path / "talk.mcruft")
    original = next(iter(doc.assets.values())).path
    stamp = original.stat().st_mtime_ns
    doc.add_file(pdf)
    doc.add_file(pdf)
    doc.save()
    assert sorted(p.name for p in (doc.path / "assets").iterdir()) == [
        "source-1.pdf",
        "source-2.pdf",
        "source.pdf",
    ]
    assert original.stat().st_mtime_ns == stamp
    doc.save(tmp_path / "copy.mcruft")
    assert len(mcruft.open(doc.path).pages) == 6


@pytest.mark.parametrize("bad", ["../source.pdf", "/tmp/source.pdf", "assets/../source.pdf"])
def test_load_when_path_escapes_then_rejects(pdf, tmp_path, bad):
    doc = mcruft.open(pdf)
    doc.save(tmp_path / "talk.mcruft")
    manifest = doc.path / "manifest.json"
    data = json.loads(manifest.read_text())
    next(iter(data["assets"].values()))["path"] = bad
    manifest.write_text(json.dumps(data))
    with pytest.raises(PackageError):
        mcruft.load(doc.path)


def test_load_when_symlink_then_rejects(pdf, tmp_path):
    doc = mcruft.open(pdf)
    doc.save(tmp_path / "talk.mcruft")
    asset = next(iter(doc.assets.values()))
    asset.path.unlink()
    asset.path.symlink_to(pdf)
    with pytest.raises(PackageError):
        mcruft.load(doc.path)


def test_refresh_when_hash_changes_then_drops_preview(pdf, tmp_path):
    doc = mcruft.open(pdf)
    doc.save(tmp_path / "talk.mcruft")
    asset = next(iter(doc.assets.values()))
    doc.pages[0].preview = asset.id
    doc.save()
    asset.path.write_bytes(asset.path.read_bytes() + b"\n")
    with pytest.warns(UserWarning, match="sha256"):
        loaded = mcruft.load(doc.path)
    assert loaded.refresh().warnings
    assert loaded.pages[0].preview is None
    loaded.save()
    assert mcruft.load(doc.path).assets[asset.id].sha256 != asset.sha256


def test_load_when_unknown_schema_then_raises(tmp_path):
    (tmp_path / "manifest.json").write_text('{"schema_version": 99}')
    with pytest.raises(UnsupportedSchema):
        mcruft.load(tmp_path)


def test_split_merge_when_shared_assets_then_independent_manifests(pdf, tmp_path):
    doc = mcruft.open(pdf)
    parts = doc.split()
    assert [p.pages[0].source["index"] for p in parts] == [0, 1]
    assert next(iter(parts[0].assets.values())).path == pdf
    merged = mcruft.merge(parts)
    merged.move_page(0, 1)
    merged.remove_pages([1])
    merged.save(tmp_path / "merged.mcruft")
    assert mcruft.load(merged.path).pages[0].source["index"] == 1
    assert len(doc.pages) == 2


def test_new_when_empty_then_saves(tmp_path: Path):
    doc = mcruft.new(title="Empty")
    doc.save(tmp_path / "empty.mcruft")
    assert mcruft.load(doc.path).meta["title"] == "Empty"


def test_save_when_replace_fails_then_preserves_manifest(pdf, tmp_path, monkeypatch):
    import os

    doc = mcruft.open(pdf)
    doc.save(tmp_path / "talk.mcruft")
    manifest = doc.path / "manifest.json"
    original = manifest.read_bytes()

    def fail(*args):
        raise OSError("replacement failed")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(PackageError, match="replacement failed"):
        doc.save()
    assert manifest.read_bytes() == original
    assert {p.name for p in doc.path.iterdir()} == {"manifest.json", "assets"}
