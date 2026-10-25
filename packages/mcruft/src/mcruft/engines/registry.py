# this_file: packages/mcruft/src/mcruft/engines/registry.py
from importlib.metadata import entry_points
from pathlib import Path

from ..report import Policy, UnsupportedRoute
from .base import Capability, Engine, EngineInfo

_registered: dict[str, Engine] = {}


def register(engine: Engine) -> None:
    _registered[engine.name] = engine


def discover() -> list[Engine]:
    engines = {ep.name: ep.load() for ep in entry_points(group="mcruft.engines")}
    engines.update(_registered)
    return list(engines.values())


def route(
    op: str, src_fmt: str, dst_fmt: str, policy: Policy, engine: str | None = None
) -> tuple[Engine, Capability]:
    if policy not in ("editable", "fidelity"):
        raise UnsupportedRoute(f"Unknown policy: {policy}")
    candidates = [
        (e, cap)
        for e in discover()
        if (engine is None or e.name == engine) and e.available()
        for cap in e.capabilities()
        if (cap.op, cap.src, cap.dst, cap.policy) == (op, src_fmt, dst_fmt, policy)
    ]
    if not candidates:
        raise UnsupportedRoute(
            f"No available route: {op} {src_fmt} -> {dst_fmt} ({policy}) engine={engine}"
        )
    order = {"native": 0, "lib": 1, "cli": 2, "mcp": 3}
    return min(candidates, key=lambda pair: (pair[1].verified_with is None, order[pair[0].kind]))


def inspect_file(path: Path) -> list[tuple[float, float]]:
    fmt = path.suffix.lower().lstrip(".")
    engine, _ = route("inspect", fmt, fmt, "editable")
    return engine.inspect(path)


def engines() -> list[EngineInfo]:
    return [
        EngineInfo(e.name, e.kind, e.available(), e.version(), e.capabilities()) for e in discover()
    ]
