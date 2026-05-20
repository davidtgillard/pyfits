"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

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
    repo = Repo(repo_dir)
    repo.init()
    repo.register_node_type("req", abstract=True)
    repo.register_node_type("REQ", extends="req")
    return repo
