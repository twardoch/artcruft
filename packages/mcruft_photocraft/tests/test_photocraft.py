# this_file: packages/mcruft_photocraft/tests/test_photocraft.py
from pathlib import Path

import pytest
from mcruft import UnsupportedRoute
from mcruft_photocraft import engine


def test_engine_when_declared_then_matches_spec():
    assert engine.name == "photocraft"
    assert engine.MIN_VERSION == "0.15.1"
    assert engine.capabilities()
    assert all(c.policy in ("editable", "fidelity") for c in engine.capabilities())
    with pytest.raises(UnsupportedRoute, match="Task 6"):
        engine.run("convert", Path("in"), Path("out"), policy="editable")
