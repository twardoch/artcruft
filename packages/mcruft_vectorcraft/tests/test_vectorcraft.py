# this_file: packages/mcruft_vectorcraft/tests/test_vectorcraft.py
from pathlib import Path

import pytest
from mcruft import UnsupportedRoute
from mcruft_vectorcraft import engine


def test_engine_when_declared_then_matches_spec():
    assert engine.name == "vectorcraft"
    assert engine.MIN_VERSION == "0.16.0"
    assert engine.capabilities()
    assert all(c.policy in ("editable", "fidelity") for c in engine.capabilities())
    with pytest.raises(UnsupportedRoute, match="Task 6"):
        engine.run("convert", Path("in"), Path("out"), policy="editable")
