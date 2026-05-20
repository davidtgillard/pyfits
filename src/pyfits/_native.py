"""ctypes bindings to libfits."""

from __future__ import annotations

import ctypes
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, cast

from pyfits._errors import FitsError, raise_for_status

if TYPE_CHECKING:
    from ctypes import CDLL

_LIB: CDLL | None = None


class FitsRepoOpenOptions(ctypes.Structure):
    """C struct FitsRepoOpenOptions."""

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


def _load_library() -> CDLL:
    """Load libfits."""
    global _LIB
    if _LIB is not None:
        return _LIB

    lib_path: Path | None = None
    for candidate in _repo_root_candidates():
        if candidate.is_file():
            lib_path = candidate
            break
    if lib_path is None:
        msg = "libfits shared library not found; set PYFITS_LIB_PATH or build ../fits"
        raise OSError(msg)

    lib = ctypes.CDLL(str(lib_path))
    _configure_lib(lib)
    _LIB = lib
    return lib


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


def lib() -> CDLL:
    """Return the loaded libfits CDLL."""
    return _load_library()


def lib_path() -> Path:
    """Return the path to the loaded libfits shared library."""
    for candidate in _repo_root_candidates():
        if candidate.is_file():
            return candidate
    msg = "libfits shared library not found"
    raise OSError(msg)


def _decode_c_string(raw: bytes | int | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8")
    return ctypes.cast(raw, ctypes.c_char_p).value.decode("utf-8")  # type: ignore[union-attr]


def version_string() -> str:
    """Return libfits package version string."""
    return _decode_c_string(lib().FITS_version_string())


def last_error() -> str:
    """Return thread-local libfits diagnostic."""
    return _decode_c_string(lib().FITS_last_error())


def open_repo(
    repo_root: str | bytes,
    *,
    registry_snapshot: str | bytes | None = None,
) -> ctypes.c_void_p:
    """Open a FitsRepo session."""
    root_b = repo_root if isinstance(repo_root, bytes) else repo_root.encode("utf-8")
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
    handle = lib().FITS_CORE_repo_open(ctypes.byref(opts))
    if not handle:
        raise FitsError(last_error() or "FITS_CORE_repo_open failed")
    return cast(ctypes.c_void_p, handle)


def close_repo(handle: ctypes.c_void_p) -> None:
    """Close a FitsRepo session."""
    lib().FITS_CORE_repo_close(handle)


def call_json(
    operation: str,
    handle: ctypes.c_void_p,
    request_json: bytes | None,
) -> tuple[int, str]:
    """Invoke a FITS_* JSON function and return (status, response_text)."""
    fn = cast(
        Callable[..., int],
        getattr(lib(), f"FITS_{operation}"),
    )
    req_ptr: ctypes.c_char_p | None = None
    if request_json is not None:
        req_ptr = ctypes.c_char_p(request_json)
    out = ctypes.c_char_p()
    status = fn(handle, req_ptr, ctypes.byref(out))
    if not out:
        raise_for_status(status, last_error())
        return status, ""
    try:
        if out.value is None:
            text = ""
        else:
            text = out.value.decode("utf-8")
    finally:
        lib().FITS_free(out)
    return status, text
