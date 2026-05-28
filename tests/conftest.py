"""Shared pytest fixtures."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_FETCH_SCRIPT = _ROOT / "scripts" / "fetch_libfits.py"
subprocess.run(
    [sys.executable, str(_FETCH_SCRIPT)],
    cwd=_ROOT,
    check=True,
)

from support import unwrap

from pyfits import Repo


@pytest.fixture
def repo_dir(tmp_path: Path) -> Path:
    """Empty directory used as a fits repository root."""
    root = tmp_path / "repo"
    root.mkdir()
    return root


@pytest.fixture
def initialized_repo(repo_dir: Path) -> Repo:
    """Repo after init and minimal type registration (abi_test pattern)."""
    repo = unwrap(Repo.open(repo_dir))
    unwrap(repo.init())
    unwrap(repo.register_node_type("req", abstract=True))
    unwrap(repo.register_node_type("REQ", extends="req"))
    return repo
