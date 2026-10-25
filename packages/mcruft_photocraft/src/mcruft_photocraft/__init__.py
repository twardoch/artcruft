# this_file: packages/mcruft_photocraft/src/mcruft_photocraft/__init__.py
from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine


class PhotocraftEngine(CliEngine):
    PRODUCT = "photocraft"
    MIN_VERSION = "0.15.1"

    def capabilities(self) -> list[Capability]:
        return [
            Capability("convert", "png", "pdf", "fidelity", "photocraft-cli 0.15.1", "Raster PDF"),
            Capability("convert", "png", "psd", "editable", "photocraft-cli 0.15.1", ""),
            Capability("convert", "png", "psd", "fidelity", "photocraft-cli 0.15.1", ""),
            Capability("convert", "psd", "png", "editable", "photocraft-cli 0.15.1", ""),
            Capability("convert", "psd", "png", "fidelity", "photocraft-cli 0.15.1", ""),
            Capability("convert", "psd", "pcraft", "editable", "photocraft-cli 0.15.1", ""),
            Capability("convert", "psd", "pcraft", "fidelity", "photocraft-cli 0.15.1", ""),
            Capability("inspect", "psd", "psd", "editable", None, "Task 6 info adapter"),
            Capability("inspect", "pcraft", "pcraft", "editable", None, "Task 6 info adapter"),
        ]


engine = PhotocraftEngine()
