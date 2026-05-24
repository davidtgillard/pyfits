"""Unit tests for repo helpers and Result propagation."""

from __future__ import annotations

from pathlib import Path

import pytest
from support import unwrap

from pyfits import FitsError, Id
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
    assert repo.new_link("l", Id("REQ-1"), Id("REQ-2")).err_value is err
    assert repo.remove(Id("REQ-1")).err_value is err
    assert repo.rename_instance(Id("REQ-1"), Id("REQ-2")).err_value is err
    assert repo.validate().err_value is err
    assert repo.output_graph().err_value is err
    assert repo.output_graph_as_json().err_value is err
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


def test_register_node_type_passes_container_and_autonumber(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    repo = unwrap(Repo.open(repo_dir))
    captured: list[dict[str, object]] = []

    def capture(
        operation: str,
        handle: object,
        request: dict[str, object] | None,
    ) -> Ok[dict[str, object]]:
        captured.append({"operation": operation, "request": request})
        return Ok({"ok": True})

    monkeypatch.setattr("pyfits.repo._json.call_and_parse", capture)
    unwrap(
        repo.register_node_type(
            "section",
            container_node="REQ",
            autonumber=False,
            create_folder=True,
        )
    )
    assert captured[0]["operation"] == "register_node_type"
    req = captured[0]["request"]
    assert isinstance(req, dict)
    assert req["container_node"] == "REQ"
    assert req["autonumber"] is False
    repo.close()


def test_new_node_serializes_target_id(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    from pyfits.models import ObjectTypeName, TargetId

    repo = unwrap(Repo.open(repo_dir))
    captured: list[dict[str, object]] = []

    def capture(
        _operation: str,
        _handle: object,
        request: dict[str, object] | None,
    ) -> Ok[dict[str, object]]:
        assert request is not None
        captured.append(dict(request))
        return Ok({"ok": True, "node_id": "login-flow"})

    monkeypatch.setattr("pyfits.repo._json.call_and_parse", capture)
    result = repo.new_node(
        ObjectTypeName("REQ"),
        container_id=Id("REQ-1"),
        target_id=TargetId("login-flow"),
    )
    assert isinstance(result, Ok)
    assert result.ok_value == Id("login-flow")
    assert captured[0]["type_name"] == "REQ"
    assert captured[0]["container_id"] == "REQ-1"
    assert captured[0]["instance_id"] == "login-flow"
    repo.close()


def test_new_link_returns_link_id(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    repo = unwrap(Repo.open(repo_dir))
    monkeypatch.setattr(
        "pyfits.repo._json.call_and_parse",
        lambda *_args, **_kwargs: Ok({"ok": True, "link_id": "depends-1"}),
    )
    result = repo.new_link("depends", Id("REQ-1"), Id("REQ-2"))
    assert isinstance(result, Ok)
    assert result.ok_value == Id("depends-1")
    repo.close()


def test_rename_instance_returns_id(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    repo = unwrap(Repo.open(repo_dir))
    monkeypatch.setattr(
        "pyfits.repo._json.call_and_parse",
        lambda *_args, **_kwargs: Ok({"ok": True, "instance_id": "auth-flow"}),
    )
    result = repo.rename_instance(Id("login-flow"), Id("auth-flow"))
    assert isinstance(result, Ok)
    assert result.ok_value == Id("auth-flow")
    repo.close()


def test_register_node_type_with_extends(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    repo = unwrap(Repo.open(repo_dir))
    captured: list[dict[str, object]] = []

    def capture(
        _operation: str,
        _handle: object,
        request: dict[str, object] | None,
    ) -> Ok[dict[str, object]]:
        assert request is not None
        captured.append(dict(request))
        return Ok({"ok": True})

    monkeypatch.setattr("pyfits.repo._json.call_and_parse", capture)
    unwrap(repo.register_node_type("REQ", extends="req"))
    assert captured[0]["extends"] == "req"
    repo.close()


def test_new_node_with_title_and_markdown(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    from pyfits.models import ObjectTypeName

    repo = unwrap(Repo.open(repo_dir))
    captured: list[dict[str, object]] = []

    def capture(
        _operation: str,
        _handle: object,
        request: dict[str, object] | None,
    ) -> Ok[dict[str, object]]:
        assert request is not None
        captured.append(dict(request))
        return Ok({"ok": True, "node_id": "REQ-1"})

    monkeypatch.setattr("pyfits.repo._json.call_and_parse", capture)
    unwrap(
        repo.new_node(
            ObjectTypeName("REQ"),
            markdown=True,
            title="Hello",
        )
    )
    assert captured[0]["markdown"] is True
    assert captured[0]["title"] == "Hello"
    repo.close()


def test_new_link_serializes_target_id(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    from pyfits.models import TargetId

    repo = unwrap(Repo.open(repo_dir))
    captured: list[dict[str, object]] = []

    def capture(
        _operation: str,
        _handle: object,
        request: dict[str, object] | None,
    ) -> Ok[dict[str, object]]:
        assert request is not None
        captured.append(dict(request))
        return Ok({"ok": True, "link_id": "depends-1"})

    monkeypatch.setattr("pyfits.repo._json.call_and_parse", capture)
    unwrap(
        repo.new_link(
            "depends",
            Id("REQ-1"),
            Id("REQ-2"),
            target_id=TargetId("my-link"),
        )
    )
    assert captured[0]["instance_id"] == "my-link"
    repo.close()


def test_validate_and_output_graph_request_options(
    monkeypatch: pytest.MonkeyPatch,
    repo_dir: Path,
) -> None:
    repo = unwrap(Repo.open(repo_dir))
    captured: list[dict[str, object]] = []

    def capture(
        _operation: str,
        _handle: object,
        request: dict[str, object] | None,
    ) -> Ok[dict[str, object]]:
        assert request is not None
        captured.append(dict(request))
        if len(captured) == 1:
            return Ok(
                {
                    "ok": True,
                    "validation_issues": [],
                    "summary": {
                        "total_validation_issues": 0,
                        "info_count": 0,
                        "warning_count": 0,
                        "error_count": 0,
                    },
                }
            )
        return Ok({"ok": True, "graph": {"nodes": [], "edges": []}})

    monkeypatch.setattr("pyfits.repo._json.call_and_parse", capture)
    unwrap(repo.validate(include_nested_subgraphs=False))
    unwrap(repo.output_graph(include_nested=True))
    unwrap(repo.output_graph_as_json(pretty_print=True, include_nested=True))
    assert captured[0]["include_nested_subgraphs"] is False
    assert captured[0]["protocol_version"] == PROTOCOL_VERSION
    assert captured[1]["include_nested"] is True
    assert "pretty_print" not in captured[1]
    assert captured[2]["include_nested"] is True
    assert "pretty_print" not in captured[2]
    repo.close()
