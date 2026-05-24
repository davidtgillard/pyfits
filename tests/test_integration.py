"""Integration tests against libfits."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from support import unwrap

from pyfits import Graph, Id, ObjectTypeName, Repo, TargetId
from pyfits.result import Err


@pytest.fixture
def repo_with_link_type(initialized_repo: Repo) -> Repo:
    unwrap(initialized_repo.register_link_type("depends", "req", "req"))
    return initialized_repo


@pytest.fixture
def nested_repo(repo_dir: Path) -> Repo:
    """Repo with root and nested types for subgraph tests."""
    repo = unwrap(Repo.open(repo_dir))
    unwrap(repo.init())
    unwrap(repo.register_node_type("req", abstract=True))
    unwrap(
        repo.register_node_type(
            "REQ",
            extends="req",
            create_folder=True,
        )
    )
    unwrap(
        repo.register_node_type(
            "section",
            container_node="REQ",
            create_folder=True,
        )
    )
    unwrap(
        repo.register_node_type(
            "item",
            container_node="section",
        )
    )
    return repo


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
    assert str(node_id).startswith("REQ")
    initialized_repo.close()


def test_new_node_without_title(initialized_repo: Repo) -> None:
    node_id = unwrap(initialized_repo.new_node(ObjectTypeName("REQ")))
    assert str(node_id).startswith("REQ")
    initialized_repo.close()


def test_new_node_opaque_target_id(initialized_repo: Repo) -> None:
    node_id = unwrap(
        initialized_repo.new_node(
            ObjectTypeName("REQ"),
            target_id=TargetId("login-flow"),
        )
    )
    assert node_id == Id("login-flow")
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
    link_id = unwrap(repo_with_link_type.new_link("depends", in_id, out_id))
    assert str(link_id).startswith("depends")
    repo_with_link_type.close()


def test_remove_node(initialized_repo: Repo) -> None:
    node_id = unwrap(initialized_repo.new_node(ObjectTypeName("REQ")))
    unwrap(initialized_repo.remove(node_id))
    initialized_repo.close()


def test_rename_instance(initialized_repo: Repo) -> None:
    unwrap(
        initialized_repo.new_node(
            ObjectTypeName("REQ"),
            target_id=TargetId("login-flow"),
        )
    )
    new_id = unwrap(initialized_repo.rename_instance(Id("login-flow"), Id("auth-flow")))
    assert new_id == Id("auth-flow")
    initialized_repo.close()


def test_output_graph(initialized_repo: Repo) -> None:
    graph = unwrap(initialized_repo.output_graph())
    assert isinstance(graph, Graph)
    pretty = unwrap(initialized_repo.output_graph(pretty_print=True))
    assert isinstance(pretty, Graph)
    initialized_repo.close()


def test_validate_exclude_nested_subgraphs(initialized_repo: Repo) -> None:
    result = unwrap(initialized_repo.validate(include_nested_subgraphs=False))
    assert result.summary.total_validation_issues >= 0
    initialized_repo.close()


def test_recursive_nested_path(nested_repo: Repo) -> None:
    unwrap(nested_repo.new_node(ObjectTypeName("REQ")))
    section_id = unwrap(
        nested_repo.new_node(
            ObjectTypeName("section"),
            container_id=Id("REQ-1"),
        )
    )
    assert section_id == Id("REQ-1/section-1")
    item_id = unwrap(
        nested_repo.new_node(
            ObjectTypeName("item"),
            container_id=section_id,
        )
    )
    assert item_id == Id("REQ-1/section-1/item-1")
    nested_repo.close()


def test_output_graph_include_nested(nested_repo: Repo) -> None:
    unwrap(nested_repo.new_node(ObjectTypeName("REQ")))
    unwrap(
        nested_repo.new_node(
            ObjectTypeName("section"),
            container_id=Id("REQ-1"),
        )
    )
    graph = unwrap(nested_repo.output_graph(include_nested=True))
    assert isinstance(graph, Graph)
    assert any(n.id == Id("REQ-1") for n in graph.nodes)
    nested_repo.close()


def test_register_node_type_with_extends(repo_dir: Path) -> None:
    repo = unwrap(Repo.open(repo_dir))
    unwrap(repo.init())
    unwrap(repo.register_node_type("req", abstract=True))
    unwrap(repo.register_node_type("REQ", extends="req"))
    repo.close()


def test_close_idempotent(initialized_repo: Repo) -> None:
    initialized_repo.close()
    initialized_repo.close()


def test_is_closed(initialized_repo: Repo) -> None:
    assert initialized_repo.is_closed is False
    initialized_repo.close()
    assert initialized_repo.is_closed is True


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
