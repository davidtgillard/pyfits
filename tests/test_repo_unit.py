"""Unit tests for repo helpers and Result propagation."""

from __future__ import annotations

from pathlib import Path

import pytest
from support import unwrap

from pyfits import FitsError
from pyfits.repo import PROTOCOL_VERSION, Repo, _with_protocol_version
from pyfits.result import Err, Ok


@pytest.mark.parametrize(
    "operation,expects_protocol",
    [
        ("validate", True),
        ("init", True),
        ("output_graph", True),
        ("register_node_type", False),
        ("new_link", False),
    ],
)
def test_with_protocol_version(operation: str, expects_protocol: bool) -> None:
    request = {"field": 1}
    result = _with_protocol_version(operation, request)
    if expects_protocol:
        assert result == {**request, "protocol_version": PROTOCOL_VERSION}
    else:
        assert result == request


def test_repo_open_success(repo_dir: Path) -> None:
    repo = unwrap(Repo.open(repo_dir))
    repo.close()


def test_repo_methods_propagate_err(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    repo = unwrap(Repo.open(repo_dir))
    err = FitsError("boom")

    def fail(*_args: object, **_kwargs: object) -> Err[FitsError]:
        return Err(err)

    monkeypatch.setattr("pyfits.repo._json.call_and_parse", fail)

    assert repo.init().err_value is err
    assert repo.register_node_type("req").err_value is err
    assert repo.register_link_type("l", "a", "b").err_value is err
    assert repo.new_link("l", "a", "b").err_value is err
    assert repo.remove("id").err_value is err
    assert repo.validate().err_value is err
    assert repo.output_graph().err_value is err
    repo.close()


def test_new_node_propagates_parse_err(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    repo = unwrap(Repo.open(repo_dir))
    monkeypatch.setattr(
        "pyfits.repo._json.call_and_parse",
        lambda *_args, **_kwargs: Ok({"ok": True}),
    )
    from pyfits.models import ObjectTypeName

    result = repo.new_node(ObjectTypeName("REQ"))
    assert isinstance(result, Err)
    repo.close()


def test_repo_open_registry_snapshot(repo_dir: Path) -> None:
    snap = repo_dir / "snap.json"
    snap.write_text("{}", encoding="utf-8")
    repo = unwrap(Repo.open(repo_dir, registry_snapshot=snap))
    repo.close()
