# this_file: packages/mcruft_deckcraft/src/mcruft_deckcraft/__init__.py
from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine


class DeckcraftEngine(CliEngine):
    PRODUCT = "deckcraft"
    MIN_VERSION = "0.10.0"

    def capabilities(self) -> list[Capability]:
        return [
            Capability(
                "convert",
                "pptx",
                "pdf",
                "editable",
                "deckcraft-cli 0.10.0",
                "Fidelity requires VectorCraft outline pass; editable rasterises slide art",
            ),
            Capability(
                "convert",
                "pptx",
                "pdf",
                "fidelity",
                "deckcraft-cli 0.10.0",
                "Fidelity requires VectorCraft outline pass; editable rasterises slide art",
            ),
            Capability("convert", "pptx", "png", "fidelity", "deckcraft-cli 0.10.0", ""),
            Capability(
                "export_pages",
                "pptx",
                "pdf",
                "editable",
                "deckcraft-cli 0.10.0",
                "Fidelity requires VectorCraft outline pass",
            ),
            Capability(
                "export_pages",
                "pptx",
                "pdf",
                "fidelity",
                "deckcraft-cli 0.10.0",
                "Fidelity requires VectorCraft outline pass",
            ),
            Capability("convert", "pptx", "deckcraft", "editable", "deckcraft-cli 0.10.0", ""),
            Capability("convert", "deckcraft", "pptx", "editable", "deckcraft-cli 0.10.0", ""),
            Capability(
                "convert",
                "pages",
                "pptx",
                "fidelity",
                "deckcraft-cli 0.10.0",
                "Pipeline: render pages to PNG before full-bleed placement",
            ),
        ]


engine = DeckcraftEngine()
