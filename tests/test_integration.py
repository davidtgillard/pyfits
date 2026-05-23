"""Integration tests against libfits."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pyfits import FitsError, ObjectTypeName, Repo


@pytest.fixture
def repo_with_link_type(initialized_repo: Repo) -> Repo:
    initialized_repo.register_link_type("depends", "req", "req")
    return initialized_repo


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
    node_id = initialized_repo.new_node(ObjectTypeName("REQ"), title="Hello")
    assert node_id.startswith("REQ")
    initialized_repo.close()


def test_new_node_without_title(initialized_repo: Repo) -> None:
    node_id = initialized_repo.new_node(ObjectTypeName("REQ"))
    assert node_id.startswith("REQ")
    initialized_repo.close()


def test_context_manager(repo_dir: Path) -> None:
    with Repo(repo_dir) as repo:
        repo.init()
        repo.register_node_type("req", abstract=True)
    # closed after exit


def test_register_link_type(repo_with_link_type: Repo) -> None:
    repo_with_link_type.close()


def test_new_link(repo_with_link_type: Repo) -> None:
    in_id = repo_with_link_type.new_node(ObjectTypeName("REQ"))
    out_id = repo_with_link_type.new_node(ObjectTypeName("REQ"))
    repo_with_link_type.new_link("depends", in_id, out_id)
    repo_with_link_type.close()


def test_remove_node(initialized_repo: Repo) -> None:
    node_id = initialized_repo.new_node(ObjectTypeName("REQ"))
    initialized_repo.remove(node_id)
    initialized_repo.close()


def test_output_graph(initialized_repo: Repo) -> None:
    graph = initialized_repo.output_graph()
    assert isinstance(graph, dict)
    pretty = initialized_repo.output_graph(pretty_print=True)
    assert isinstance(pretty, dict)
    initialized_repo.close()


def test_register_node_type_with_extends(repo_dir: Path) -> None:
    repo = Repo(repo_dir)
    repo.init()
    repo.register_node_type("req", abstract=True)
    repo.register_node_type("REQ", extends="req")
    repo.close()


def test_close_idempotent(initialized_repo: Repo) -> None:
    initialized_repo.close()
    initialized_repo.close()


def test_use_after_close_raises(initialized_repo: Repo) -> None:
    initialized_repo.close()
    with pytest.raises(RuntimeError, match="repository session is closed"):
        initialized_repo.init()


def test_validate_exclude_link_endpoints(initialized_repo: Repo) -> None:
    result = initialized_repo.validate(include_link_endpoints=False)
    assert result.summary.total_validation_issues >= 0
    initialized_repo.close()


def test_repo_with_registry_snapshot(repo_dir: Path) -> None:
    with Repo(repo_dir) as repo:
        repo.init()
        repo.register_node_type("req", abstract=True)
        repo.register_node_type("REQ", extends="req")

    registry = repo_dir / ".fits" / "registry.json"
    assert registry.is_file()
    snapshot = repo_dir / "registry.snapshot.json"
    shutil.copy(registry, snapshot)

    with Repo(repo_dir, registry_snapshot=snapshot) as repo:
        result = repo.validate()
        assert result.summary.total_validation_issues >= 0
