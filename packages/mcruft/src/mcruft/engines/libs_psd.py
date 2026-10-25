# this_file: packages/mcruft/src/mcruft/engines/libs_psd.py
"""Optional PSD canvas inspection without a product CLI."""

import importlib.util
import struct
from importlib.metadata import version
from pathlib import Path

from ..report import EngineFailed
from .base import Capability
from .cli import pixel_scale


def capabilities() -> list[Capability]:
    if importlib.util.find_spec("psd_tools") is None:
        return []
    return [
        Capability("inspect", "psd", "psd", policy, f"lib psd-tools {version('psd-tools')}")
        for policy in ("editable", "fidelity")
    ]


def inspect(src: Path) -> list[tuple[float, float]]:
    from psd_tools import PSDImage
    from psd_tools.constants import Resource

    try:
        psd = PSDImage.open(src)
        resolution = psd.image_resources.get_data(Resource.RESOLUTION_INFO)
        # PSD resolution values are 16.16 fixed-point pixels per inch.
        dpi = (
            (resolution.horizontal / 65536, resolution.vertical / 65536) if resolution else (72, 72)
        )
        return [(psd.width / pixel_scale(dpi[0]), psd.height / pixel_scale(dpi[1]))]
    except (OSError, ValueError, EOFError, struct.error) as exc:
        raise EngineFailed(f"lib psd-tools inspect: {exc}") from exc
