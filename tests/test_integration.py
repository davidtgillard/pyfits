"""Integration tests against libfits."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from support import unwrap

from pyfits import ObjectTypeName, Repo
from pyfits.result import Err


@pytest.fixture
def repo_with_link_type(initialized_repo: Repo) -> Repo:
    unwrap(initialized_repo.register_link_type("depends", "req", "req"))
    return initialized_repo


def test_init_and_validate(initialized_repo: Repo) -> None:
    result = unwrap(initialized_repo.validate())
    assert result.summary.total_validation_issues >= 0
    initialized_repo.close()


def test_init_twice_returns_err(repo_dir: Path) -> None:
    repo = unwrap(Repo.open(repo_dir))
    with repo:
        unwrap(repo.init())
        second = repo.init()
        assert isinstance(second, Err)


def test_new_node(initialized_repo: Repo) -> None:
    node_id = unwrap(initialized_repo.new_node(ObjectTypeName("REQ"), title="Hello"))
    assert node_id.startswith("REQ")
    initialized_repo.close()


def test_new_node_without_title(initialized_repo: Repo) -> None:
    node_id = unwrap(initialized_repo.new_node(ObjectTypeName("REQ")))
    assert node_id.startswith("REQ")
    initialized_repo.close()


def test_context_manager(repo_dir: Path) -> None:
    repo = unwrap(Repo.open(repo_dir))
    with repo:
        unwrap(repo.init())
        unwrap(repo.register_node_type("req", abstract=True))
    # closed after exit


def test_register_link_type(repo_with_link_type: Repo) -> None:
    repo_with_link_type.close()


def test_new_link(repo_with_link_type: Repo) -> None:
    in_id = unwrap(repo_with_link_type.new_node(ObjectTypeName("REQ")))
    out_id = unwrap(repo_with_link_type.new_node(ObjectTypeName("REQ")))
    unwrap(repo_with_link_type.new_link("depends", in_id, out_id))
    repo_with_link_type.close()


def test_remove_node(initialized_repo: Repo) -> None:
    node_id = unwrap(initialized_repo.new_node(ObjectTypeName("REQ")))
    unwrap(initialized_repo.remove(node_id))
    initialized_repo.close()


def test_output_graph(initialized_repo: Repo) -> None:
    graph = unwrap(initialized_repo.output_graph())
    assert isinstance(graph, dict)
    pretty = unwrap(initialized_repo.output_graph(pretty_print=True))
    assert isinstance(pretty, dict)
    initialized_repo.close()


def test_register_node_type_with_extends(repo_dir: Path) -> None:
    repo = unwrap(Repo.open(repo_dir))
    unwrap(repo.init())
    unwrap(repo.register_node_type("req", abstract=True))
    unwrap(repo.register_node_type("REQ", extends="req"))
    repo.close()


def test_close_idempotent(initialized_repo: Repo) -> None:
    initialized_repo.close()
    initialized_repo.close()


def test_use_after_close_raises(initialized_repo: Repo) -> None:
    initialized_repo.close()
    with pytest.raises(RuntimeError, match="repository session is closed"):
        initialized_repo.init()


def test_validate_exclude_link_endpoints(initialized_repo: Repo) -> None:
    result = unwrap(initialized_repo.validate(include_link_endpoints=False))
    assert result.summary.total_validation_issues >= 0
    initialized_repo.close()


def test_repo_with_registry_snapshot(repo_dir: Path) -> None:
    repo = unwrap(Repo.open(repo_dir))
    with repo:
        unwrap(repo.init())
        unwrap(repo.register_node_type("req", abstract=True))
        unwrap(repo.register_node_type("REQ", extends="req"))

    registry = repo_dir / ".fits" / "registry.json"
    assert registry.is_file()
    snapshot = repo_dir / "registry.snapshot.json"
    shutil.copy(registry, snapshot)

    snap_repo = unwrap(Repo.open(repo_dir, registry_snapshot=snapshot))
    with snap_repo:
        result = unwrap(snap_repo.validate())
        assert result.summary.total_validation_issues >= 0


def test_repo_open_failure(monkeypatch: pytest.MonkeyPatch, repo_dir: Path) -> None:
    from pyfits import _native
    from pyfits._errors import FitsError

    monkeypatch.setattr(
        _native,
        "open_repo",
        lambda *_args, **_kwargs: Err(FitsError("open failed")),
    )
    result = Repo.open(repo_dir)
    assert isinstance(result, Err)
    assert str(result.err_value) == "open failed"
