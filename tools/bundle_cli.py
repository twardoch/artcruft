# this_file: tools/bundle_cli.py
"""Build a self-contained macOS CLI wheel without running a packaging backend."""

import argparse
import base64
import csv
import hashlib
import io
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path

PRODUCTS = ("vectorcraft", "deckcraft", "photocraft", "pdfcraft", "designcraft")


def wheel_hash(data: bytes) -> str:
    return "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()


def bundle(
    product: str,
    binary: Path | None = None,
    out: Path = Path("dist"),
    arch: str = "arm64",
    license_dir: Path | None = None,
) -> Path:
    if product not in PRODUCTS or arch != "arm64":
        raise ValueError("Only batch-1 products and arm64 wheels are supported")
    binary = binary or shutil.which(f"{product}-cli")
    if binary is None:
        raise FileNotFoundError(f"Cannot find {product}-cli")
    binary = Path(binary).absolute()
    from_version = subprocess.run(
        [str(binary), "--version"], check=True, capture_output=True, text=True, timeout=30
    )
    # Keep this tool runnable without installing mcruft.
    import re

    match = re.search(r"\b\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?", from_version.stdout)
    if match is None:
        raise ValueError(f"No version number in {from_version.stdout!r}")
    version = match[0]
    package = f"mcruft_{product}_bin"
    info = f"{package}-{version}.dist-info"
    tag = f"py3-none-macosx_11_0_{arch}"
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out) as temporary:
        copied = Path(temporary) / binary.name
        shutil.copy2(binary, copied)
        lipo = shutil.which("lipo")
        if lipo:
            result = subprocess.run(
                [lipo, "-info", str(copied)],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if (
                result.returncode == 0
                and "Non-fat" not in result.stdout
                and "Architectures" in result.stdout
            ):
                subprocess.run(
                    [lipo, str(copied), "-thin", arch, "-output", str(copied)],
                    check=True,
                    capture_output=True,
                    timeout=30,
                )
        init = (
            f"# this_file: {package}/__init__.py\nfrom pathlib import Path\n"
            f'BIN = Path(__file__).parent / "bin" / "{product}-cli"\n'
            "if not BIN.stat().st_mode & 0o111:\n    BIN.chmod(BIN.stat().st_mode | 0o755)\n"
        )
        files = {
            f"{package}/__init__.py": init.encode(),
            f"{package}/bin/{product}-cli": copied.read_bytes(),
            f"{info}/METADATA": (
                f"Metadata-Version: 2.3\nName: mcruft-{product}-bin\n"
                f"Version: {version}\nRequires-Python: >=3.12\n\n"
            ).encode(),
            f"{info}/WHEEL": (
                "Wheel-Version: 1.0\nGenerator: mcruft.bundle_cli\n"
                f"Root-Is-Purelib: false\nTag: {tag}\n"
            ).encode(),
        }
    if license_dir is not None:
        for path in sorted(Path(license_dir).rglob("*")):
            if path.is_file():
                files[f"{info}/licenses/{path.relative_to(license_dir).as_posix()}"] = (
                    path.read_bytes()
                )
    record = io.StringIO(newline="")
    writer = csv.writer(record, lineterminator="\n")
    writer.writerows((name, wheel_hash(data), len(data)) for name, data in files.items())
    writer.writerow((f"{info}/RECORD", "", ""))
    files[f"{info}/RECORD"] = record.getvalue().encode()
    wheel = out / f"{package}-{version}-{tag}.whl"
    with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            entry = zipfile.ZipInfo(name)
            entry.create_system = 3
            mode = 0o755 if name.endswith(f"/bin/{product}-cli") else 0o644
            entry.external_attr = (stat.S_IFREG | mode) << 16
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED)
    return wheel


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product", choices=PRODUCTS)
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--out", type=Path, default=Path("dist"))
    parser.add_argument("--arch", choices=["arm64"], default="arm64")
    parser.add_argument("--license-dir", type=Path)
    args = parser.parse_args()
    print(bundle(args.product, args.binary, args.out, args.arch, args.license_dir))


if __name__ == "__main__":
    main()
