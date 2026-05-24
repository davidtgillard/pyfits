"""Repository session API."""

from __future__ import annotations

import ctypes
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pyfits import _json, _native
from pyfits._errors import FitsError
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
from pyfits.result import Err, Ok, Result

PROTOCOL_VERSION = 1
"""JSON protocol version sent to libfits for supported operations."""

# libfits JSON parsers that accept protocol_version (ignore_unknown_fields).
_OPS_WITH_PROTOCOL_VERSION = frozenset({"validate", "init", "output_graph"})


def _call_parsed[T](
    operation: str,
    handle: ctypes.c_void_p,
    request: dict[str, Any] | None,
    parser: Callable[[dict[str, Any]], Result[T, FitsError]],
) -> Result[T, FitsError]:
    return _json.call_and_parse(operation, handle, request).and_then(parser)


def _with_protocol_version(operation: str, request: dict[str, Any]) -> dict[str, Any]:
    if operation in _OPS_WITH_PROTOCOL_VERSION:
        return {**request, "protocol_version": PROTOCOL_VERSION}
    return request


class Repo:
    """Open fits repository session (one handle per thread).

    Open sessions with :meth:`open`. Use as a context manager or call
    :meth:`close` explicitly when finished.
    """

    def __init__(self, handle: ctypes.c_void_p, path: Path) -> None:
        """Store an already-open repository session handle.

        Args:
            handle: Native session handle from :func:`pyfits._native.open_repo`.
            path: Resolved repository root path.
        """
        self._handle: ctypes.c_void_p | None = handle
        self._path = path

    @staticmethod
    def open(
        path: str | Path,
        *,
        registry_snapshot: str | Path | None = None,
    ) -> Result[Repo, FitsError]:
        """Open a repository at ``path``.

        The directory must exist on disk before calling :meth:`init`.

        Args:
            path: Filesystem path to the repository root directory.
            registry_snapshot: Optional path to a registry snapshot file. When
                provided, libfits validates the live registry against this
                snapshot for the lifetime of the session.

        Returns:
            ``Ok(Repo)`` on success, or ``Err(FitsError)`` when opening fails.
        """
        resolved = Path(path).resolve()
        snap: str | None = None
        if registry_snapshot is not None:
            snap = str(Path(registry_snapshot).resolve())
        match _native.open_repo(
            str(resolved).encode("utf-8"),
            registry_snapshot=snap.encode("utf-8") if snap else None,
        ):
            case Err(error):
                return Err(error)
            case Ok(handle):
                return Ok(Repo(handle, resolved))

    def __enter__(self) -> Repo:
        """Enter the context manager and return this session.

        Returns:
            This open repository session.
        """
        return self

    def __exit__(self, *_exc: object) -> None:
        """Close the session when leaving a ``with`` block."""
        self.close()

    def close(self) -> None:
        """Close the repository session and release the native handle."""
        if self._handle is not None:
            _native.close_repo(self._handle)
            self._handle = None

    @property
    def is_closed(self) -> bool:
        """Return whether this session has been closed.

        Returns:
            ``True`` after :meth:`close` (including context-manager exit);
            ``False`` while the native handle is still active.
        """
        return self._handle is None

    def _require_handle(self) -> ctypes.c_void_p:
        if self._handle is None:
            msg = "repository session is closed"
            raise RuntimeError(msg)
        return self._handle

    def init(
        self,
        *,
        init_git: bool = False,
        edit_gitignore: bool = False,
    ) -> Result[None, FitsError]:
        """Initialize an empty directory as a fits repository.

        Args:
            init_git: When ``True``, initialize a git repository in the root.
            edit_gitignore: When ``True``, create or update ``.gitignore``.

        Returns:
            ``Ok(None)`` on success, or ``Err(FitsError)`` when libfits reports
            an operation failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = _with_protocol_version(
            "init",
            {
                "init_git": init_git,
                "edit_gitignore": edit_gitignore,
            },
        )
        match _json.call_and_parse("init", self._require_handle(), request):
            case Err(error):
                return Err(error)
            case Ok(_):
                return Ok(None)

    def register_node_type(
        self,
        type_name: str,
        *,
        abstract: bool = False,
        extends: str | None = None,
        create_folder: bool = False,
        container_node: str | None = None,
        autonumber: bool = True,
    ) -> Result[None, FitsError]:
        """Register a node type in the repository registry.

        Args:
            type_name: Registry name for the node type.
            abstract: When ``True``, mark the type as abstract.
            extends: Optional parent type name for inheritance.
            create_folder: When ``True``, create on-disk folders for the type.
            container_node: When set, register a nested-scoped type for nodes
                whose type matches this container name.
            autonumber: When ``True`` (default), omitting ``target_id`` on
                create allocates ``{type_name}-{n}``.

        Returns:
            ``Ok(None)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request: dict[str, Any] = {
            "type_name": type_name,
            "abstract": abstract,
            "create_folder": create_folder,
            "autonumber": autonumber,
        }
        if extends is not None:
            request["extends"] = extends
        if container_node is not None:
            request["container_node"] = container_node
        match _json.call_and_parse(
            "register_node_type",
            self._require_handle(),
            request,
        ):
            case Err(error):
                return Err(error)
            case Ok(_):
                return Ok(None)

    def register_link_type(
        self,
        link_type: str,
        in_type: str,
        out_type: str,
        *,
        create_folder: bool = False,
    ) -> Result[None, FitsError]:
        """Register a link type in the repository registry.

        Nested vs root scope is determined by the registered endpoint types; libfits
        treats nested link registration as the same operation.

        Args:
            link_type: Registry name for the link type.
            in_type: Required input node type name.
            out_type: Required output node type name.
            create_folder: When ``True``, create on-disk folders for the type.

        Returns:
            ``Ok(None)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = {
            "link_type": link_type,
            "in_type": in_type,
            "out_type": out_type,
            "create_folder": create_folder,
        }
        match _json.call_and_parse(
            "register_link_type",
            self._require_handle(),
            request,
        ):
            case Err(error):
                return Err(error)
            case Ok(_):
                return Ok(None)

    def new_node(
        self,
        type_name: ObjectTypeName,
        *,
        container_id: Id | None = None,
        target_id: TargetId | None = None,
        markdown: bool = False,
        title: str | None = None,
    ) -> Result[Id, FitsError]:
        """Create a new node in the repository graph.

        Args:
            type_name: Registered object type name for the new node.
            container_id: Optional parent canonical id for nested create.
            target_id: Optional explicit single-segment id; omit for autonumber
                allocation.
            markdown: When ``True``, create the node as markdown-backed content.
            title: Optional human-readable node title.

        Returns:
            ``Ok(Id)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request: dict[str, Any] = {
            "type_name": type_name.value,
            "markdown": markdown,
        }
        if container_id is not None:
            request["container_id"] = container_id.value
        if target_id is not None:
            request["target_id"] = target_id.value
        if title is not None:
            request["title"] = title
        return _call_parsed(
            "new_node",
            self._require_handle(),
            request,
            parse_new_node_id,
        )

    def new_link(
        self,
        link_type: str,
        in_id: Id,
        out_id: Id,
        *,
        target_id: TargetId | None = None,
    ) -> Result[Id, FitsError]:
        """Create a link between two existing nodes.

        Args:
            link_type: Registered link type name.
            in_id: Input endpoint canonical node id.
            out_id: Output endpoint canonical node id.
            target_id: Optional explicit single-segment link id; omit for
                autonumber allocation.

        Returns:
            ``Ok(Id)`` with the new link id on success, or ``Err(FitsError)`` on
            failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request: dict[str, Any] = {
            "link_type": link_type,
            "in_id": in_id.value,
            "out_id": out_id.value,
        }
        if target_id is not None:
            request["target_id"] = target_id.value
        return _call_parsed(
            "new_link",
            self._require_handle(),
            request,
            parse_new_link_id,
        )

    def remove(self, object_id: Id) -> Result[None, FitsError]:
        """Remove a node or link by id.

        Args:
            object_id: Canonical graph object id to remove.

        Returns:
            ``Ok(None)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = {
            "object_id": object_id.value,
        }
        match _json.call_and_parse("remove", self._require_handle(), request):
            case Err(error):
                return Err(error)
            case Ok(_):
                return Ok(None)

    def rename_instance(
        self,
        old_id: Id,
        new_id: Id,
    ) -> Result[Id, FitsError]:
        """Rename a live instance id (GUID stable).

        Args:
            old_id: Current canonical instance id.
            new_id: New canonical instance id in the same scope.

        Returns:
            ``Ok(Id)`` with the new id on success, or ``Err(FitsError)`` on
            failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = {
            "old_id": old_id.value,
            "new_id": new_id.value,
        }
        return _call_parsed(
            "rename_instance",
            self._require_handle(),
            request,
            parse_rename_instance_id,
        )

    def validate(
        self,
        *,
        include_link_endpoints: bool = True,
        include_nested_subgraphs: bool = True,
    ) -> Result[ValidateResult, FitsError]:
        """Validate the repository graph.

        Args:
            include_link_endpoints: When ``True``, validate link endpoint nodes.
            include_nested_subgraphs: When ``True``, validate nested subgraphs.

        Returns:
            ``Ok(ValidateResult)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = _with_protocol_version(
            "validate",
            {
                "include_link_endpoints": include_link_endpoints,
                "include_nested_subgraphs": include_nested_subgraphs,
            },
        )
        return _call_parsed(
            "validate",
            self._require_handle(),
            request,
            parse_validate_result,
        )

    def output_graph(
        self,
        *,
        include_nested: bool = False,
    ) -> Result[Graph, FitsError]:
        """Serialize the repository graph.

        Args:
            include_nested: When ``True``, merge nested nodes and edges into the
                graph arrays.

        Returns:
            ``Ok(Graph)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = _with_protocol_version(
            "output_graph",
            {
                "include_nested": include_nested,
            },
        )
        return _call_parsed(
            "output_graph",
            self._require_handle(),
            request,
            parse_output_graph,
        )

    def output_graph_as_json(
        self,
        *,
        pretty_print: bool = False,
        include_nested: bool = False,
    ) -> Result[str, FitsError]:
        """Serialize the repository graph as a JSON string.

        Useful for debugging or piping graph JSON into fits tooling.

        Args:
            pretty_print: When ``True``, indent the JSON for human-readable
                output.
            include_nested: When ``True``, merge nested nodes and edges into the
                graph arrays.

        Returns:
            ``Ok(json_text)`` containing the graph object on success, or
            ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = _with_protocol_version(
            "output_graph",
            {
                "include_nested": include_nested,
            },
        )
        return _call_parsed(
            "output_graph",
            self._require_handle(),
            request,
            lambda doc: format_output_graph_json(doc, pretty_print=pretty_print),
        )
