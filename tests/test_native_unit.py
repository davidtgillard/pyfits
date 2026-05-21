"""Unit tests for pyfits._native edge paths."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pyfits import _native
from pyfits._errors import FitsError


@pytest.fixture(autouse=True)
def reset_lib() -> None:
    _native._LIB = None
    yield
    _native._LIB = None


def _bundled_lib() -> Path:
    root = Path(__file__).resolve().parents[1]
    path = root / "src" / "pyfits" / "_lib" / "libfits.so"
    if not path.is_file():
        pytest.skip("bundled libfits.so not found")
    return path


def test_repo_root_candidates_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lib = _bundled_lib()
    monkeypatch.setenv("PYFITS_LIB_PATH", str(lib))
    assert _native._repo_root_candidates() == [lib]


def test_repo_root_candidates_win32(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYFITS_LIB_PATH", raising=False)
    monkeypatch.delenv("LIBFITS_LIB_PATH", raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    candidates = _native._repo_root_candidates()
    assert candidates[0].name == "libfits.dll"


def test_load_library_skips_missing_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lib = _bundled_lib()
    missing = Path("/nonexistent/libfits.so")
    monkeypatch.setattr(
        _native,
        "_repo_root_candidates",
        lambda: [missing, lib],
    )
    loaded = _native.lib()
    assert loaded is not None


def test_load_library_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        _native,
        "_repo_root_candidates",
        lambda: [Path("/nonexistent/libfits.so")],
    )
    with pytest.raises(OSError, match="libfits shared library not found"):
        _native.lib()


def test_lib_path_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        _native,
        "_repo_root_candidates",
        lambda: [Path("/nonexistent/libfits.so")],
    )
    with pytest.raises(OSError, match="libfits shared library not found"):
        _native.lib_path()


def test_lib_path_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    lib = _bundled_lib()
    monkeypatch.setenv("PYFITS_LIB_PATH", str(lib))
    assert _native.lib_path() == lib


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, ""),
        (b"hello", "hello"),
    ],
)
def test_decode_c_string_none_and_bytes(raw: bytes | None, expected: str) -> None:
    assert _native._decode_c_string(raw) == expected


def test_decode_c_string_int_pointer() -> None:
    encoded = ctypes.create_string_buffer(b"from-pointer")
    raw = ctypes.cast(encoded, ctypes.c_void_p).value
    assert _native._decode_c_string(raw) == "from-pointer"


def test_open_repo_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    lib = _bundled_lib()
    monkeypatch.setenv("PYFITS_LIB_PATH", str(lib))
    mock_lib = _native.lib()
    monkeypatch.setattr(
        mock_lib,
        "FITS_CORE_repo_open",
        lambda _opts: None,
    )
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    with pytest.raises(FitsError, match="FITS_CORE_repo_open failed"):
        _native.open_repo(b"/tmp/repo")


def test_open_repo_bytes_registry_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    lib = _bundled_lib()
    monkeypatch.setenv("PYFITS_LIB_PATH", str(lib))
    mock_lib = _native.lib()
    captured: dict[str, object] = {}

    def fake_open(opts: object) -> ctypes.c_void_p:
        opts_ptr = ctypes.cast(opts, ctypes.POINTER(_native.FitsRepoOpenOptions))
        captured["snapshot"] = opts_ptr.contents.registry_snapshot_path
        return ctypes.c_void_p(1)

    monkeypatch.setattr(mock_lib, "FITS_CORE_repo_open", fake_open)
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    handle = _native.open_repo(b"/tmp/repo", registry_snapshot=b"/tmp/snap")
    assert handle.value == 1
    assert captured["snapshot"] == b"/tmp/snap"


def test_call_json_no_request_json(monkeypatch: pytest.MonkeyPatch) -> None:
    lib = _bundled_lib()
    monkeypatch.setenv("PYFITS_LIB_PATH", str(lib))
    mock_lib = _native.lib()
    captured: dict[str, object] = {}

    def fake_init(
        _handle: ctypes.c_void_p,
        req: ctypes.c_char_p | None,
        out: object,
    ) -> int:
        captured["req"] = req
        out_ptr = ctypes.cast(out, ctypes.POINTER(ctypes.c_char_p))
        out_ptr[0] = ctypes.c_char_p(b'{"ok": true}')
        return 0

    mock_lib.FITS_init = fake_init
    mock_lib.FITS_free = lambda _ptr: None
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    status, text = _native.call_json("init", ctypes.c_void_p(1), None)
    assert captured["req"] is None
    assert status == 0
    assert text == '{"ok": true}'


def test_call_json_no_output(monkeypatch: pytest.MonkeyPatch) -> None:
    lib = _bundled_lib()
    monkeypatch.setenv("PYFITS_LIB_PATH", str(lib))
    mock_lib = _native.lib()

    def fake_init(
        _handle: ctypes.c_void_p,
        _req: ctypes.c_char_p | None,
        _out: object,
    ) -> int:
        return -1

    mock_lib.FITS_init = fake_init
    mock_lib.FITS_free = lambda _ptr: None
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    monkeypatch.setattr(_native, "last_error", lambda: "empty response")
    with pytest.raises(FitsError, match="empty response"):
        _native.call_json("init", ctypes.c_void_p(1), b"{}")


def test_call_json_null_output_value(monkeypatch: pytest.MonkeyPatch) -> None:
    lib = _bundled_lib()
    monkeypatch.setenv("PYFITS_LIB_PATH", str(lib))
    mock_lib = _native.lib()

    def fake_init(
        _handle: ctypes.c_void_p,
        _req: ctypes.c_char_p | None,
        out: object,
    ) -> int:
        out_ptr = ctypes.cast(out, ctypes.POINTER(ctypes.c_char_p))
        out_ptr[0] = None
        return 0

    mock_lib.FITS_init = fake_init
    mock_lib.FITS_free = lambda _ptr: None
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    status, text = _native.call_json("init", ctypes.c_void_p(1), b"{}")
    assert status == 0
    assert text == ""


def test_version_string_uses_decode(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_version_string.return_value = b"1.2.3"
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    assert _native.version_string() == "1.2.3"
