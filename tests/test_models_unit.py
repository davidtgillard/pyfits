"""Unit tests for response model parsers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from pyfits._errors import FitsSchemaError
from pyfits.models import (
    ObjectTypeName,
    ValidateResult,
    parse_new_node_id,
    parse_output_graph,
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
        (_valid_validate_doc(), "REQ-1", 2),
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
    object_id: str | None,
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
        (parse_new_node_id, {"ok": True, "node_id": 1}, "missing node_id"),
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


def test_parse_new_node_id_success() -> None:
    result = parse_new_node_id({"ok": True, "node_id": "REQ-42"})
    assert isinstance(result, Ok)
    assert result.ok_value == "REQ-42"


def test_parse_output_graph_success() -> None:
    graph = {"nodes": [], "links": []}
    result = parse_output_graph({"ok": True, "graph": graph})
    assert isinstance(result, Ok)
    assert result.ok_value == graph


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
