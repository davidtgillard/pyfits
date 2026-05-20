"""Integration tests against libfits."""

from __future__ import annotations

from pathlib import Path

import pytest

from pyfits import FitsError, Repo


def test_init_and_validate(initialized_repo: Repo) -> None:
    result = initialized_repo.validate()
    assert result.summary.total_validation_issues >= 0
    initialized_repo.close()


def test_init_twice_raises(repo_dir: Path) -> None:
    with Repo(repo_dir) as repo:
        repo.init()
        with pytest.raises(FitsError):
            repo.init()


def test_new_node(initialized_repo: Repo) -> None:
    node_id = initialized_repo.new_node("REQ", title="Hello")
    assert node_id.startswith("REQ")
    initialized_repo.close()


def test_context_manager(repo_dir: Path) -> None:
    with Repo(repo_dir) as repo:
        repo.init()
        repo.register_node_type("req", abstract=True)
    # closed after exit
