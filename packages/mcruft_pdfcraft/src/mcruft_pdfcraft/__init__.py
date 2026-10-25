# this_file: packages/mcruft_pdfcraft/src/mcruft_pdfcraft/__init__.py
from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine


class PdfcraftEngine(CliEngine):
    PRODUCT = "pdfcraft"
    MIN_VERSION = "0.13.0"

    def capabilities(self) -> list[Capability]:
        return [
            Capability("render", "pdf", "png", "fidelity", "pdfcraft-cli 0.13.0", ""),
        ]


engine = PdfcraftEngine()
