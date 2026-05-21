"""Unit tests for repo helpers."""

from __future__ import annotations

import pytest

from pyfits.repo import PROTOCOL_VERSION, _with_protocol_version


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
