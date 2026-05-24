"""Unit tests for response model parsers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from pyfits._errors import FitsSchemaError
from pyfits.models import (
    Graph,
    Id,
    ObjectTypeName,
    TargetId,
    ValidateResult,
    format_output_graph_json,
    parse_new_link_id,
    parse_new_node_id,
    parse_output_graph,
    parse_rename_instance_id,
    parse_validate_result,
)
from pyfits.result import Err, Ok

_VALID_SUMMARY: dict[str, int] = {
    "total_validation_issues": 3,
    "info_count": 1,
    "warning_count": 1,
    "error_count": 1,
}


def _valid_validate_doc(**overrides: Any) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "ok": True,
        "validation_issues": [
            {
                "severity": "info",
                "code": "i",
                "message": "info msg",
                "object_id": "REQ-1",
            },
            {"severity": "warn", "code": "w", "message": "warn msg"},
            {"severity": "error", "code": "e", "message": "error msg"},
        ],
        "summary": dict(_VALID_SUMMARY),
        "protocol_version": 2,
    }
    doc.update(overrides)
    return doc


@pytest.mark.parametrize(
    "doc,match",
    [
        ({"ok": False}, "expected ok=true"),
        ({"ok": True}, "missing validation_issues array"),
        (
            {"ok": True, "validation_issues": [], "summary": "bad"},
            "missing summary",
        ),
        (
            {
                "ok": True,
                "validation_issues": ["bad"],
                "summary": _VALID_SUMMARY,
            },
            "must be an object",
        ),
        (
            {
                "ok": True,
                "validation_issues": [
                    {"severity": "critical", "code": "c", "message": "m"},
                ],
                "summary": _VALID_SUMMARY,
            },
            "invalid validation issue severity",
        ),
        (
            {
                "ok": True,
                "validation_issues": [{"severity": "info", "message": "m"}],
                "summary": _VALID_SUMMARY,
            },
            "missing code or message",
        ),
        (
            {
                "ok": True,
                "validation_issues": [{"severity": "info", "code": "c", "message": 1}],
                "summary": _VALID_SUMMARY,
            },
            "missing code or message",
        ),
        (
            {
                "ok": True,
                "validation_issues": [],
                "summary": {**_VALID_SUMMARY, "total_validation_issues": "x"},
            },
            "summary.total_validation_issues must be an integer",
        ),
        (
            {
                "ok": True,
                "validation_issues": [],
                "summary": {**_VALID_SUMMARY, "info_count": "x"},
            },
            "summary.info_count must be an integer",
        ),
        (
            {
                "ok": True,
                "validation_issues": [],
                "summary": {**_VALID_SUMMARY, "warning_count": "x"},
            },
            "summary.warning_count must be an integer",
        ),
        (
            {
                "ok": True,
                "validation_issues": [],
                "summary": {**_VALID_SUMMARY, "error_count": "x"},
            },
            "summary.error_count must be an integer",
        ),
    ],
)
def test_parse_validate_result_returns_err(doc: dict[str, Any], match: str) -> None:
    result = parse_validate_result(doc)
    assert isinstance(result, Err)
    assert isinstance(result.err_value, FitsSchemaError)
    assert match in str(result.err_value)


@pytest.mark.parametrize(
    "doc,object_id,protocol_version",
    [
        (_valid_validate_doc(), Id("REQ-1"), 2),
        (
            _valid_validate_doc(
                validation_issues=[
                    {"severity": "info", "code": "i", "message": "m"},
                ],
                summary={
                    "total_validation_issues": 1,
                    "info_count": 1,
                    "warning_count": 0,
                    "error_count": 0,
                },
                protocol_version="not-int",
            ),
            None,
            None,
        ),
    ],
)
def test_parse_validate_result_success(
    doc: dict[str, Any],
    object_id: Id | None,
    protocol_version: int | None,
) -> None:
    result = parse_validate_result(doc)
    assert isinstance(result, Ok)
    assert isinstance(result.ok_value, ValidateResult)
    assert result.ok_value.protocol_version == protocol_version
    if object_id is not None:
        assert result.ok_value.validation_issues[0].object_id == object_id
    else:
        assert result.ok_value.validation_issues[0].object_id is None


@pytest.mark.parametrize(
    "parser,doc,match",
    [
        (parse_new_node_id, {"ok": True}, "missing node_id"),
        (parse_new_node_id, {"ok": True, "node_id": 1}, "node_id must be a string"),
        (parse_new_link_id, {"ok": True}, "missing link_id"),
        (parse_rename_instance_id, {"ok": True}, "missing instance_id"),
        (parse_output_graph, {"ok": True}, "missing graph object"),
        (parse_output_graph, {"ok": True, "graph": []}, "missing graph object"),
    ],
)
def test_parser_returns_err(
    parser: Callable[[dict[str, Any]], Any],
    doc: dict[str, Any],
    match: str,
) -> None:
    result = parser(doc)
    assert isinstance(result, Err)
    assert match in str(result.err_value)


def test_parse_new_node_id_strips_title_suffix() -> None:
    result = parse_new_node_id({"ok": True, "node_id": "REQ-1 Hello"})
    assert isinstance(result, Ok)
    assert result.ok_value == Id("REQ-1")


def test_parse_new_node_id_success() -> None:
    result = parse_new_node_id({"ok": True, "node_id": "REQ-42"})
    assert isinstance(result, Ok)
    assert result.ok_value == Id("REQ-42")


def test_parse_new_link_id_success() -> None:
    result = parse_new_link_id({"ok": True, "link_id": "depends-1"})
    assert isinstance(result, Ok)
    assert result.ok_value == Id("depends-1")


def test_parse_rename_instance_id_success() -> None:
    result = parse_rename_instance_id({"ok": True, "instance_id": "auth-flow"})
    assert isinstance(result, Ok)
    assert result.ok_value == Id("auth-flow")


def test_parse_output_graph_success() -> None:
    graph_doc = {
        "nodes": [{"id": "REQ-1"}],
        "edges": [
            {
                "from_id": "REQ-1",
                "to_id": "REQ-2",
                "kind": "registered_link",
                "link_type": "depends",
            }
        ],
    }
    result = parse_output_graph({"ok": True, "graph": graph_doc})
    assert isinstance(result, Ok)
    graph = result.ok_value
    assert isinstance(graph, Graph)
    assert graph.nodes[0].id == Id("REQ-1")
    assert graph.edges[0].from_id == Id("REQ-1")


def test_format_output_graph_json_compact() -> None:
    graph_doc = {"nodes": [{"id": "REQ-1"}], "edges": []}
    result = format_output_graph_json({"ok": True, "graph": graph_doc})
    assert isinstance(result, Ok)
    assert result.ok_value == '{"nodes":[{"id":"REQ-1"}],"edges":[]}'


def test_format_output_graph_json_pretty() -> None:
    graph_doc = {"nodes": [{"id": "REQ-1"}], "edges": []}
    result = format_output_graph_json(
        {"ok": True, "graph": graph_doc},
        pretty_print=True,
    )
    assert isinstance(result, Ok)
    assert result.ok_value.startswith("{\n")
    assert result.ok_value.endswith("\n")


def test_format_output_graph_json_missing_graph() -> None:
    result = format_output_graph_json({"ok": True})
    assert isinstance(result, Err)
    assert isinstance(result.err_value, FitsSchemaError)


def test_parse_output_graph_nested_nodes() -> None:
    graph_doc = {
        "nodes": [
            {"id": "REQ-1"},
            {"id": "REQ-1/section-1", "parent_id": "REQ-1"},
        ],
        "edges": [],
    }
    result = parse_output_graph({"ok": True, "graph": graph_doc})
    assert isinstance(result, Ok)
    nested = result.ok_value.nodes[1]
    assert nested.id == Id("REQ-1/section-1")
    assert nested.parent_id == Id("REQ-1")


@pytest.mark.parametrize(
    "value",
    [
        "login-flow",
        "section-1",
        "REQ-1",
    ],
)
def test_target_id_accepts_valid_values(value: str) -> None:
    target = TargetId(value)
    assert target.value == value


@pytest.mark.parametrize(
    "value,match",
    [
        ("", "non-empty"),
        ("REQ-1/section-1", "single segment"),
        ("a b", "whitespace"),
        ("file.md", "must not contain '.'"),
    ],
)
def test_target_id_rejects_invalid_values(value: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        TargetId(value)


@pytest.mark.parametrize(
    "value",
    [
        "REQ-1",
        "login-flow",
        "REQ-1/section-1/item-1",
    ],
)
def test_id_accepts_valid_values(value: str) -> None:
    parsed = Id(value)
    assert parsed.value == value
    assert parsed.segments == tuple(value.split("/"))


@pytest.mark.parametrize(
    "value,match",
    [
        ("", "non-empty"),
        ("REQ-1/", "empty path segments"),
        ("/REQ-1", "empty path segments"),
        ("REQ-1//section-1", "empty path segments"),
    ],
)
def test_id_rejects_invalid_values(value: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        Id(value)


def test_id_join() -> None:
    joined = Id.join(Id("REQ-1"), TargetId("section-1"))
    assert joined == Id("REQ-1/section-1")


@pytest.mark.parametrize(
    "value",
    [
        "REQ",
        "req",
        "sys",
        "REQ_foo",
        "My-Subsystem",
        "a1",
        "Z",
        "REQ-1",
    ],
)
def test_object_type_name_accepts_valid_values(value: str) -> None:
    type_name = ObjectTypeName(value)
    assert type_name.value == value
    assert str(type_name) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "1abc",
        "123",
        "_foo",
        "hello world",
        "REQ.foo",
        "-My-Subsystem",
    ],
)
def test_object_type_name_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match="object type name must"):
        ObjectTypeName(value)


def test_parse_output_graph_invalid_edge_kind() -> None:
    graph_doc = {
        "nodes": [{"id": "REQ-1"}],
        "edges": [
            {
                "from_id": "REQ-1",
                "to_id": "REQ-2",
                "kind": "unknown",
                "link_type": "depends",
            }
        ],
    }
    result = parse_output_graph({"ok": True, "graph": graph_doc})
    assert isinstance(result, Err)
    assert "invalid graph edge kind" in str(result.err_value)


def test_parse_output_graph_invalid_node_id() -> None:
    graph_doc = {"nodes": [{"id": "bad id"}], "edges": []}
    result = parse_output_graph({"ok": True, "graph": graph_doc})
    assert isinstance(result, Err)
    assert "invalid node.id" in str(result.err_value)


def test_id_try_parse_returns_none_for_invalid() -> None:
    assert Id.try_parse("bad id") is None


def test_parse_output_graph_nested_edge() -> None:
    graph_doc = {
        "nodes": [],
        "edges": [
            {
                "id": "REQ-1/depends-1",
                "parent_id": "REQ-1",
                "from_id": "REQ-1/section-1",
                "to_id": "REQ-1/section-2",
                "kind": "registered_link",
                "link_type": "depends",
            }
        ],
    }
    result = parse_output_graph({"ok": True, "graph": graph_doc})
    assert isinstance(result, Ok)
    edge = result.ok_value.edges[0]
    assert edge.id == Id("REQ-1/depends-1")
    assert edge.parent_id == Id("REQ-1")


@pytest.mark.parametrize(
    "value,match",
    [
        ("", "non-empty"),
        ("a b", "whitespace"),
        ("file.md", "must not contain '.'"),
        ("bad/id", "single segment"),
    ],
)
def test_target_id_validation_messages(value: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        TargetId(value)


@pytest.mark.parametrize(
    "value,match",
    [
        ("bad id", "whitespace"),
        ("file.md", "must not contain '.'"),
    ],
)
def test_id_rejects_opaque_invalid_segment(value: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        Id(value)


def test_parse_output_graph_missing_nodes_array() -> None:
    result = parse_output_graph({"ok": True, "graph": {"edges": []}})
    assert isinstance(result, Err)
    assert "missing nodes array" in str(result.err_value)


def test_parse_output_graph_node_not_object() -> None:
    result = parse_output_graph(
        {"ok": True, "graph": {"nodes": ["bad"], "edges": []}},
    )
    assert isinstance(result, Err)
    assert "graph node must be an object" in str(result.err_value)


def test_parse_output_graph_edge_missing_from_id() -> None:
    graph_doc = {
        "nodes": [],
        "edges": [
            {
                "to_id": "REQ-2",
                "kind": "registered_link",
                "link_type": "depends",
            }
        ],
    }
    result = parse_output_graph({"ok": True, "graph": graph_doc})
    assert isinstance(result, Err)
    assert "edge.from_id" in str(result.err_value)


def test_validate_segment_forbidden_char() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        TargetId("bad*id")


def test_parse_validate_result_non_string_object_id() -> None:
    doc = _valid_validate_doc(
        validation_issues=[
            {
                "severity": "info",
                "code": "i",
                "message": "m",
                "object_id": 123,
            },
        ],
        summary={
            "total_validation_issues": 1,
            "info_count": 1,
            "warning_count": 0,
            "error_count": 0,
        },
    )
    result = parse_validate_result(doc)
    assert isinstance(result, Ok)
    assert result.ok_value.validation_issues[0].object_id is None


def test_id_and_target_str() -> None:
    assert str(Id("REQ-1")) == "REQ-1"
    assert str(TargetId("login-flow")) == "login-flow"


def test_parse_validate_result_invalid_object_id_becomes_none() -> None:
    doc = _valid_validate_doc(
        validation_issues=[
            {
                "severity": "info",
                "code": "i",
                "message": "m",
                "object_id": "bad id",
            },
        ],
        summary={
            "total_validation_issues": 1,
            "info_count": 1,
            "warning_count": 0,
            "error_count": 0,
        },
    )
    result = parse_validate_result(doc)
    assert isinstance(result, Ok)
    assert result.ok_value.validation_issues[0].object_id is None


def test_parse_output_graph_missing_edges_array() -> None:
    result = parse_output_graph({"ok": True, "graph": {"nodes": []}})
    assert isinstance(result, Err)
    assert "missing edges array" in str(result.err_value)


def test_parse_output_graph_edge_not_object() -> None:
    result = parse_output_graph(
        {"ok": True, "graph": {"nodes": [], "edges": ["bad"]}},
    )
    assert isinstance(result, Err)
    assert "graph edge must be an object" in str(result.err_value)


def test_parse_output_graph_edge_missing_to_id() -> None:
    graph_doc = {
        "nodes": [],
        "edges": [
            {
                "from_id": "REQ-1",
                "kind": "registered_link",
                "link_type": "depends",
            }
        ],
    }
    result = parse_output_graph({"ok": True, "graph": graph_doc})
    assert isinstance(result, Err)
    assert "edge.to_id" in str(result.err_value)


def test_parse_output_graph_edge_missing_link_type() -> None:
    graph_doc = {
        "nodes": [],
        "edges": [
            {
                "from_id": "REQ-1",
                "to_id": "REQ-2",
                "kind": "registered_link",
            }
        ],
    }
    result = parse_output_graph({"ok": True, "graph": graph_doc})
    assert isinstance(result, Err)
    assert "missing link_type" in str(result.err_value)


def test_parse_output_graph_invalid_optional_ids() -> None:
    graph_doc = {
        "nodes": [{"id": "REQ-1", "parent_id": "bad id"}],
        "edges": [
            {
                "from_id": "REQ-1",
                "to_id": "REQ-2",
                "kind": "registered_link",
                "link_type": "depends",
                "id": "bad id",
                "parent_id": "bad id",
            }
        ],
    }
    result = parse_output_graph({"ok": True, "graph": graph_doc})
    assert isinstance(result, Err)


def test_id_and_target_id_parse_helpers() -> None:
    assert Id.parse("REQ-1") == Id("REQ-1")
    assert TargetId.parse("login-flow") == TargetId("login-flow")


@pytest.mark.parametrize(
    "value,match",
    [
        ("bad\\id", "path separators"),
        ("bad.", "must not end"),
        ("x\x01", "control"),
    ],
)
def test_id_segment_extra_validation(value: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        Id(value)


def test_wire_id_from_response_qualified_with_title() -> None:
    from pyfits.models import _wire_id_from_response

    assert _wire_id_from_response("REQ-1/section-1 Title") == "REQ-1/section-1"


def test_parse_new_node_id_invalid_canonical() -> None:
    result = parse_new_node_id({"ok": True, "node_id": "file.md"})
    assert isinstance(result, Err)
