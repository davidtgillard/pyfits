"""ctypes bindings to libfits."""

from __future__ import annotations

import ctypes
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, cast

from pyfits._errors import FitsError, error_from_status, lib_not_found_error
from pyfits.result import Err, Ok, Result

if TYPE_CHECKING:
    from ctypes import CDLL

_LIB: CDLL | None = None


class FitsRepoOpenOptions(ctypes.Structure):
    """C struct ``FitsRepoOpenOptions`` passed to ``FITS_CORE_repo_open``.

    Attributes:
        struct_size: Size of this structure in bytes.
        repo_root: NUL-terminated repository root path.
        registry_snapshot_path: Optional NUL-terminated registry snapshot path.
    """

    _fields_: ClassVar[list[tuple[str, type]]] = [
        ("struct_size", ctypes.c_uint32),
        ("repo_root", ctypes.c_char_p),
        ("registry_snapshot_path", ctypes.c_char_p),
    ]


def _repo_root_candidates() -> list[Path]:
    """Paths to search for libfits.so."""
    env = os.environ.get("PYFITS_LIB_PATH") or os.environ.get("LIBFITS_LIB_PATH")
    if env:
        return [Path(env)]

    candidates: list[Path] = []
    if sys.platform == "win32":
        candidates.append(Path(__file__).resolve().parent / "_lib" / "libfits.dll")
    else:
        candidates.append(Path(__file__).resolve().parent / "_lib" / "libfits.so")

    pyfits_root = Path(__file__).resolve().parents[2]
    candidates.append(pyfits_root.parent / "fits" / "zig-out" / "lib" / "libfits.so")
    return candidates


def load_library() -> Result[CDLL, FitsError]:
    """Load libfits and return the configured CDLL handle.

    Returns:
        Loaded library on success, or ``Err(FitsError)`` when not found or load
        fails.
    """
    global _LIB
    if _LIB is not None:
        return Ok(_LIB)

    lib_path: Path | None = None
    for candidate in _repo_root_candidates():
        if candidate.is_file():
            lib_path = candidate
            break
    if lib_path is None:
        msg = "libfits shared library not found; set PYFITS_LIB_PATH or build ../fits"
        return Err(lib_not_found_error(msg))

    try:
        lib = ctypes.CDLL(str(lib_path))
    except OSError as exc:
        return Err(FitsError(str(exc), code="lib_load_failed"))
    _configure_lib(lib)
    _LIB = lib
    return Ok(lib)


def lib() -> CDLL:
    """Return the loaded libfits CDLL.

    Returns:
        Loaded and configured libfits shared library handle.

    Raises:
        RuntimeError: When :func:`load_library` returns ``Err``.
    """
    match load_library():
        case Ok(loaded):
            return loaded
        case Err(error):
            msg = str(error)
            raise RuntimeError(msg)


def _configure_lib(lib: CDLL) -> None:
    """Set ctypes signatures for exported symbols."""
    lib.FITS_api_version.argtypes = []
    lib.FITS_api_version.restype = ctypes.c_uint32

    lib.FITS_version_string.argtypes = []
    lib.FITS_version_string.restype = ctypes.c_char_p

    lib.FITS_free.argtypes = [ctypes.c_void_p]
    lib.FITS_free.restype = None

    lib.FITS_last_error.argtypes = []
    lib.FITS_last_error.restype = ctypes.c_char_p

    lib.FITS_CORE_repo_open.argtypes = [ctypes.POINTER(FitsRepoOpenOptions)]
    lib.FITS_CORE_repo_open.restype = ctypes.c_void_p

    lib.FITS_CORE_repo_close.argtypes = [ctypes.c_void_p]
    lib.FITS_CORE_repo_close.restype = None

    json_repo_args = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p),
    ]
    json_repo_restype = ctypes.c_int32

    for name in (
        "FITS_init",
        "FITS_validate",
        "FITS_output_graph",
        "FITS_new_node",
        "FITS_new_link",
        "FITS_remove_obj",
        "FITS_register_node_type",
        "FITS_register_link_type",
    ):
        fn = getattr(lib, name)
        fn.argtypes = json_repo_args
        fn.restype = json_repo_restype

    schema_names = (
        "FITS_validate_request_schema",
        "FITS_validate_response_schema",
        "FITS_output_graph_request_schema",
        "FITS_new_node_request_schema",
        "FITS_new_node_response_schema",
        "FITS_new_link_request_schema",
        "FITS_remove_request_schema",
        "FITS_init_request_schema",
        "FITS_register_node_type_request_schema",
        "FITS_register_link_type_request_schema",
        "FITS_error_response_schema",
    )
    for name in schema_names:
        fn = getattr(lib, name)
        fn.argtypes = []
        fn.restype = ctypes.c_char_p


def lib_path() -> Result[Path, FitsError]:
    """Return the path to the libfits shared library.

    Returns:
        ``Ok(path)`` for the first discovered library, or ``Err(FitsError)`` when
        none is found.
    """
    for candidate in _repo_root_candidates():
        if candidate.is_file():
            return Ok(candidate)
    return Err(lib_not_found_error("libfits shared library not found"))


def _decode_c_string(raw: bytes | int | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8")
    return ctypes.cast(raw, ctypes.c_char_p).value.decode("utf-8")  # type: ignore[union-attr]


def version_string() -> Result[str, FitsError]:
    """Return the libfits package version string.

    Returns:
        ``Ok(version)`` from ``FITS_version_string()``, or ``Err(FitsError)`` when
        the library cannot be loaded.
    """
    match load_library():
        case Ok(loaded):
            return Ok(_decode_c_string(loaded.FITS_version_string()))
        case Err(error):
            return Err(error)


def last_error() -> Result[str, FitsError]:
    """Return the thread-local libfits diagnostic string.

    Returns:
        ``Ok(message)`` for the current thread diagnostic, or ``Err(FitsError)``
        when the library cannot be loaded.
    """
    match load_library():
        case Ok(loaded):
            return Ok(_decode_c_string(loaded.FITS_last_error()))
        case Err(error):
            return Err(error)


def open_repo(
    repo_root: str | bytes,
    *,
    registry_snapshot: str | bytes | None = None,
) -> Result[ctypes.c_void_p, FitsError]:
    """Open a FitsRepo session.

    Args:
        repo_root: Repository root path as UTF-8 text or bytes.
        registry_snapshot: Optional registry snapshot path as UTF-8 text or
            bytes.

    Returns:
        ``Ok(handle)`` on success, or ``Err(FitsError)`` on failure.
    """
    match load_library():
        case Err(error):
            return Err(error)
        case Ok(loaded):
            root_b = (
                repo_root if isinstance(repo_root, bytes) else repo_root.encode("utf-8")
            )
            snap_b: bytes | None = None
            if registry_snapshot is not None:
                snap_b = (
                    registry_snapshot
                    if isinstance(registry_snapshot, bytes)
                    else registry_snapshot.encode("utf-8")
                )
            opts = FitsRepoOpenOptions(
                struct_size=ctypes.sizeof(FitsRepoOpenOptions),
                repo_root=root_b,
                registry_snapshot_path=snap_b,
            )
            handle = loaded.FITS_CORE_repo_open(ctypes.byref(opts))
            if not handle:
                match last_error():
                    case Ok(message):
                        msg = message or "FITS_CORE_repo_open failed"
                    case Err(error):
                        msg = str(error)
                return Err(FitsError(msg))
            return Ok(cast(ctypes.c_void_p, handle))


def close_repo(handle: ctypes.c_void_p) -> None:
    """Close a FitsRepo session.

    Args:
        handle: Repository session handle returned by :func:`open_repo`.
    """
    lib().FITS_CORE_repo_close(handle)


def call_json(
    operation: str,
    handle: ctypes.c_void_p,
    request_json: bytes | None,
) -> Result[tuple[int, str], FitsError]:
    """Invoke a ``FITS_*`` JSON function and return status and response text.

    Args:
        operation: C function suffix after ``FITS_`` (e.g. ``validate``,
            ``remove_obj``).
        handle: Open repository session handle.
        request_json: Optional compact UTF-8 JSON request body.

    Returns:
        ``Ok((status, text))`` on success. ``response_text`` is empty when
        libfits returns no JSON body. ``Err(FitsError)`` when the library cannot
        be loaded or libfits returns a negative status with no JSON body.
    """
    match load_library():
        case Err(error):
            return Err(error)
        case Ok(loaded):
            fn = cast(
                Callable[..., int],
                getattr(loaded, f"FITS_{operation}"),
            )
            req_ptr: ctypes.c_char_p | None = None
            if request_json is not None:
                req_ptr = ctypes.c_char_p(request_json)
            out = ctypes.c_char_p()
            status = fn(handle, req_ptr, ctypes.byref(out))
            if not out:
                match last_error():
                    case Ok(message):
                        err = error_from_status(status, message)
                    case Err(error):
                        return Err(error)
                if err is not None:
                    return Err(err)
                return Ok((status, ""))
            try:
                if out.value is None:
                    text = ""
                else:
                    text = out.value.decode("utf-8")
            finally:
                loaded.FITS_free(out)
            return Ok((status, text))
