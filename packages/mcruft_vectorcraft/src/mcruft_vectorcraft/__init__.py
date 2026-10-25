# this_file: packages/mcruft_vectorcraft/src/mcruft_vectorcraft/__init__.py
from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine


class VectorcraftEngine(CliEngine):
    PRODUCT = "vectorcraft"
    MIN_VERSION = "0.16.0"

    def capabilities(self) -> list[Capability]:
        return [
            Capability("convert", "svg", "pdf", "editable", "vectorcraft-cli 0.16.0", ""),
            Capability("convert", "svg", "pdf", "fidelity", "vectorcraft-cli 0.16.0", ""),
            Capability("convert", "svg", "png", "fidelity", "vectorcraft-cli 0.16.0", ""),
            Capability("convert", "pdf", "svg", "editable", "vectorcraft-cli 0.16.0", ""),
            Capability("convert", "pdf", "svg", "fidelity", "vectorcraft-cli 0.16.0", ""),
            Capability(
                "outline_text",
                "pdf",
                "pdf",
                "fidelity",
                "vectorcraft-cli 0.16.0",
                "Re-import may drop links, annotations and forms",
            ),
            Capability("convert", "pdf", "psd", "fidelity", "vectorcraft-cli 0.16.0", ""),
            Capability(
                "inspect", "vectorcraft", "vectorcraft", "editable", None, "Task 6 info adapter"
            ),
            Capability("inspect", "ai", "ai", "editable", None, "Task 6 info adapter"),
        ]


engine = VectorcraftEngine()
