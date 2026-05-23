"""Repository session API."""

from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any

from pyfits import _json, _native
from pyfits._errors import FitsError
from pyfits.models import (
    ObjectTypeName,
    ValidateResult,
    parse_new_node_id,
    parse_output_graph,
    parse_validate_result,
)
from pyfits.result import Err, Ok, Result

PROTOCOL_VERSION = 1
"""JSON protocol version sent to libfits for supported operations."""

# libfits JSON parsers that accept protocol_version (ignore_unknown_fields).
_OPS_WITH_PROTOCOL_VERSION = frozenset({"validate", "init", "output_graph"})


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
    ) -> Result[None, FitsError]:
        """Initialize an empty directory as a fits repository.

        Args:
            no_interactive: When ``True``, skip interactive prompts.
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
                "no_interactive": no_interactive,
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
    ) -> Result[None, FitsError]:
        """Register a node type in the repository registry.

        Args:
            type_name: Registry name for the node type.
            abstract: When ``True``, mark the type as abstract.
            extends: Optional parent type name for inheritance.
            create_folder: When ``True``, create on-disk folders for the type.

        Returns:
            ``Ok(None)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request: dict[str, Any] = {
            "type_name": type_name,
            "abstract": abstract,
            "create_folder": create_folder,
        }
        if extends is not None:
            request["extends"] = extends
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
        id_prefix: ObjectTypeName,
        *,
        markdown: bool = False,
        title: str | None = None,
    ) -> Result[str, FitsError]:
        """Create a new node in the repository graph.

        Args:
            id_prefix: Registered object type name used to allocate the new id.
            markdown: When ``True``, create the node as markdown-backed content.
            title: Optional human-readable node title.

        Returns:
            ``Ok(node_id)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request: dict[str, Any] = {
            "id_prefix": id_prefix.value,
            "markdown": markdown,
        }
        if title is not None:
            request["title"] = title
        match _json.call_and_parse("new_node", self._require_handle(), request):
            case Err(error):
                return Err(error)
            case Ok(doc):
                return parse_new_node_id(doc)

    def new_link(
        self,
        link_type: str,
        in_id: str,
        out_id: str,
    ) -> Result[None, FitsError]:
        """Create a link between two existing nodes.

        Args:
            link_type: Registered link type name.
            in_id: Input endpoint node id.
            out_id: Output endpoint node id.

        Returns:
            ``Ok(None)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = {
            "link_type": link_type,
            "in_id": in_id,
            "out_id": out_id,
        }
        match _json.call_and_parse("new_link", self._require_handle(), request):
            case Err(error):
                return Err(error)
            case Ok(_):
                return Ok(None)

    def remove(self, object_id: str) -> Result[None, FitsError]:
        """Remove a node or link by id.

        Args:
            object_id: Graph object id to remove.

        Returns:
            ``Ok(None)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = {
            "object_id": object_id,
        }
        match _json.call_and_parse("remove", self._require_handle(), request):
            case Err(error):
                return Err(error)
            case Ok(_):
                return Ok(None)

    def validate(
        self,
        *,
        include_link_endpoints: bool = True,
    ) -> Result[ValidateResult, FitsError]:
        """Validate the repository graph.

        Args:
            include_link_endpoints: When ``True``, validate link endpoint nodes.

        Returns:
            ``Ok(ValidateResult)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = _with_protocol_version(
            "validate",
            {"include_link_endpoints": include_link_endpoints},
        )
        match _json.call_and_parse("validate", self._require_handle(), request):
            case Err(error):
                return Err(error)
            case Ok(doc):
                return parse_validate_result(doc)

    def output_graph(
        self,
        *,
        pretty_print: bool = False,
    ) -> Result[dict[str, Any], FitsError]:
        """Serialize the repository graph.

        Args:
            pretty_print: When ``True``, request pretty-printed JSON from libfits.

        Returns:
            ``Ok(graph)`` on success, or ``Err(FitsError)`` on failure.

        Raises:
            RuntimeError: When the session is already closed.
        """
        request = _with_protocol_version("output_graph", {"pretty_print": pretty_print})
        match _json.call_and_parse("output_graph", self._require_handle(), request):
            case Err(error):
                return Err(error)
            case Ok(doc):
                return parse_output_graph(doc)
