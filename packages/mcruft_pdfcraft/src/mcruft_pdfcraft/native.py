# this_file: packages/mcruft_pdfcraft/src/mcruft_pdfcraft/native.py
"""Optional adapter for the pinned PdfCraft PyO3 binding."""

from importlib import import_module
from pathlib import Path

from mcruft.engines.base import Capability, Engine
from mcruft.engines.cli import page_indexes
from mcruft.report import EngineFailed, EngineUnavailable, Policy, Report, UnsupportedRoute


class PdfcraftNativeEngine(Engine):
    name, kind = "pdfcraft-native", "native"

    def available(self) -> bool:
        try:
            import_module("mcruft_pdfcraft_native")
        except ImportError:
            return False
        return True

    def capabilities(self) -> list[Capability]:
        return [
            Capability(op, "pdf", "pdf", policy, "pdfcraft-native adapter tests")
            for op in ("extract_pages", "combine")
            for policy in ("editable", "fidelity")
        ]

    def run(self, op: str, src: Path, dst: Path, *, policy: Policy, **opts) -> Report:
        try:
            native = import_module("mcruft_pdfcraft_native")
        except ImportError as exc:
            raise EngineUnavailable(
                "Install mcruft_pdfcraft_native to use pdfcraft-native"
            ) from exc
        src, dst = Path(src).absolute(), Path(dst).absolute()
        if (
            op not in ("extract_pages", "combine")
            or policy not in ("editable", "fidelity")
            or src.suffix.lower() != ".pdf"
            or dst.suffix.lower() != ".pdf"
        ):
            raise UnsupportedRoute(f"{self.name}: {op} {src.suffix} -> {dst.suffix} ({policy})")
        try:
            if op == "extract_pages":
                pages = page_indexes(opts.get("pages"), native.page_count(str(src)))
                native.extract(str(src), pages, str(dst))
            else:
                paths = [str(Path(path).absolute()) for path in opts.get("paths", [src])]
                native.combine(paths, str(dst))
        except (OSError, RuntimeError) as exc:
            raise EngineFailed(f"{self.name} {op}: {exc}") from exc
        return Report(op, policy, self.name, outputs=[dst])


engine = PdfcraftNativeEngine()
