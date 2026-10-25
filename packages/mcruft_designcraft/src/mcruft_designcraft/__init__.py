# this_file: packages/mcruft_designcraft/src/mcruft_designcraft/__init__.py
from mcruft.engines.base import Capability
from mcruft.engines.cli import CliEngine


class DesigncraftEngine(CliEngine):
    PRODUCT = "designcraft"
    MIN_VERSION = "0.12.0"

    def capabilities(self) -> list[Capability]:
        return [
            Capability(
                "convert",
                "idml",
                "pdf",
                "editable",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "idml",
                "pdf",
                "fidelity",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "idml",
                "png",
                "editable",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "idml",
                "png",
                "fidelity",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "idml",
                "pptx",
                "editable",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "idml",
                "pptx",
                "fidelity",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "designcraft",
                "pdf",
                "editable",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "designcraft",
                "pdf",
                "fidelity",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "designcraft",
                "png",
                "editable",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "designcraft",
                "png",
                "fidelity",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "designcraft",
                "pptx",
                "editable",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
            Capability(
                "convert",
                "designcraft",
                "pptx",
                "fidelity",
                None,
                "Unverified file input; fidelity requires outline pass",
            ),
        ]


engine = DesigncraftEngine()
