# this_file: packages/mcruft/src/mcruft/engines/registry.py
from importlib.metadata import entry_points
from pathlib import Path

from ..report import EngineUnavailable, McruftError, Policy, UnsupportedRoute
from .base import Capability, Engine, EngineInfo, normalize_format

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
    src_fmt, dst_fmt = normalize_format(src_fmt), normalize_format(dst_fmt)
    available_engines = discover()
    if engine is not None and not any(
        e.name == engine and e.available() for e in available_engines
    ):
        raise EngineUnavailable(f"Engine unavailable: {engine}")
    candidates = [
        (e, cap)
        for e in available_engines
        if (engine is None or e.name == engine) and e.available()
        for cap in e.capabilities()
        if (cap.op, normalize_format(cap.src), normalize_format(cap.dst), cap.policy)
        == (op, src_fmt, dst_fmt, policy)
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
    result = []
    for engine in discover():
        try:
            available, version = engine.available(), engine.version()
        except McruftError:
            available, version = False, None
        result.append(
            EngineInfo(engine.name, engine.kind, available, version, engine.capabilities())
        )
    return result
