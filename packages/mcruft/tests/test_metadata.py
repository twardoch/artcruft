# this_file: packages/mcruft/tests/test_metadata.py
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("path", sorted((ROOT / "packages").glob("*/pyproject.toml")))
def test_package_declares_apache_license(path):
    assert tomllib.loads(path.read_text())["project"].get("license") == "Apache-2.0"


@pytest.mark.parametrize("product", ["vectorcraft", "pdfcraft"])
def test_product_declares_direct_pdf_dependency(product):
    path = ROOT / "packages" / f"mcruft_{product}" / "pyproject.toml"
    assert "pypdf" in tomllib.loads(path.read_text())["project"]["dependencies"]
