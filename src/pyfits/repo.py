"""Repository session API."""

from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any

from pyfits import _json, _native
from pyfits.models import (
    ValidateResult,
    parse_new_node_id,
    parse_output_graph,
    parse_validate_result,
)

PROTOCOL_VERSION = 1

# libfits JSON parsers that accept protocol_version (ignore_unknown_fields).
_OPS_WITH_PROTOCOL_VERSION = frozenset({"validate", "init", "output_graph"})


def _with_protocol_version(operation: str, request: dict[str, Any]) -> dict[str, Any]:
    if operation in _OPS_WITH_PROTOCOL_VERSION:
        return {**request, "protocol_version": PROTOCOL_VERSION}
    return request


class Repo:
    """Open fits repository session (one handle per thread)."""

    def __init__(
        self,
        path: str | Path,
        *,
        registry_snapshot: str | Path | None = None,
    ) -> None:
        """Open a repository at ``path`` (created on disk before ``init``)."""
        self._path = Path(path).resolve()
        snap: str | None = None
        if registry_snapshot is not None:
            snap = str(Path(registry_snapshot).resolve())
        self._handle: ctypes.c_void_p | None = _native.open_repo(
            str(self._path).encode("utf-8"),
            registry_snapshot=snap.encode("utf-8") if snap else None,
        )

    def __enter__(self) -> Repo:
        """Enter context manager."""
        return self

    def __exit__(self, *_exc: object) -> None:
        """Close the session on context exit."""
        self.close()

    def close(self) -> None:
        """Close the repository session."""
        if self._handle is not None:
            _native.close_repo(self._handle)
            self._handle = None

    def _require_handle(self) -> ctypes.c_void_p:
        if self._handle is None:
            msg = "repository session is closed"
            raise RuntimeError(msg)
        return self._handle

    def init(
        self,
        *,
        no_interactive: bool = True,
        init_git: bool = False,
        edit_gitignore: bool = False,
    ) -> None:
        """Initialize an empty directory as a fits repository."""
        request = _with_protocol_version(
            "init",
            {
                "no_interactive": no_interactive,
                "init_git": init_git,
                "edit_gitignore": edit_gitignore,
            },
        )
        _json.call_and_parse("init", self._require_handle(), request)

    def register_node_type(
        self,
        type_name: str,
        *,
        abstract: bool = False,
        extends: str | None = None,
        create_folder: bool = False,
    ) -> None:
        """Register a node type in the repository registry."""
        request: dict[str, Any] = {
            "type_name": type_name,
            "abstract": abstract,
            "create_folder": create_folder,
        }
        if extends is not None:
            request["extends"] = extends
        _json.call_and_parse("register_node_type", self._require_handle(), request)

    def register_link_type(
        self,
        link_type: str,
        in_type: str,
        out_type: str,
        *,
        create_folder: bool = False,
    ) -> None:
        """Register a link type in the repository registry."""
        request = {
            "link_type": link_type,
            "in_type": in_type,
            "out_type": out_type,
            "create_folder": create_folder,
        }
        _json.call_and_parse("register_link_type", self._require_handle(), request)

    def new_node(
        self,
        id_prefix: str,
        *,
        markdown: bool = False,
        title: str | None = None,
    ) -> str:
        """Create a new node.

        Returns:
            Allocated node id.
        """
        request: dict[str, Any] = {
            "id_prefix": id_prefix,
            "markdown": markdown,
        }
        if title is not None:
            request["title"] = title
        doc = _json.call_and_parse("new_node", self._require_handle(), request)
        return parse_new_node_id(doc)

    def new_link(self, link_type: str, in_id: str, out_id: str) -> None:
        """Create a link between two nodes."""
        request = {
            "link_type": link_type,
            "in_id": in_id,
            "out_id": out_id,
        }
        _json.call_and_parse("new_link", self._require_handle(), request)

    def remove(self, object_id: str) -> None:
        """Remove a node or link by id."""
        request = {
            "object_id": object_id,
        }
        _json.call_and_parse("remove", self._require_handle(), request)

    def validate(self, *, include_link_endpoints: bool = True) -> ValidateResult:
        """Validate the repository graph.

        Returns:
            Validation issues and aggregate severity counts.
        """
        request = _with_protocol_version(
            "validate",
            {"include_link_endpoints": include_link_endpoints},
        )
        doc = _json.call_and_parse("validate", self._require_handle(), request)
        return parse_validate_result(doc)

    def output_graph(self, *, pretty_print: bool = False) -> dict[str, Any]:
        """Serialize the repository graph.

        Returns:
            Graph object from the libfits response (JSON-serializable dict).
        """
        request = _with_protocol_version("output_graph", {"pretty_print": pretty_print})
        doc = _json.call_and_parse("output_graph", self._require_handle(), request)
        return parse_output_graph(doc)
