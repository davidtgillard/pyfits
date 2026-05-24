"""Unit tests for package metadata."""

from __future__ import annotations

import importlib
import importlib.metadata

import pytest


def test_public_exports_include_id_types() -> None:
    import pyfits

    assert hasattr(pyfits, "Id")
    assert hasattr(pyfits, "TargetId")
    assert hasattr(pyfits, "Graph")
    assert "Id" in pyfits.__all__


def test_version_fallback_when_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_not_found(_name: str) -> str:
        msg = "not installed"
        raise importlib.metadata.PackageNotFoundError(msg)

    monkeypatch.setattr(importlib.metadata, "version", _raise_not_found)
    import pyfits

    importlib.reload(pyfits)
    assert pyfits.__version__ == "0.0.0+unknown"
    importlib.reload(pyfits)
