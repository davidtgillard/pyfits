#!/usr/bin/env python3
"""Download libfits.so from a GitHub release (configured in pyproject.toml)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import TypedDict


class LibfitsConfig(TypedDict):
    """libfits GitHub release settings from ``[tool.pyfits.libfits]``."""

    repo: str
    release: str
    asset: str
    manifest: str
    manifest_sha256_asset: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_libfits_section(text: str) -> dict[str, str]:
    """Parse ``[tool.pyfits.libfits]`` without tomllib (Python 3.9 compatibility)."""
    in_section = False
    values: dict[str, str] = {}
    key_value = re.compile(r'^([\w-]+)\s*=\s*"(.*)"\s*(?:#.*)?$')
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[tool.pyfits.libfits]":
            in_section = True
            continue
        if not in_section:
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            break
        if not stripped or stripped.startswith("#"):
            continue
        match = key_value.match(stripped)
        if match is None:
            msg = f"Unsupported line in [tool.pyfits.libfits]: {stripped!r}"
            raise SystemExit(msg)
        values[match.group(1)] = match.group(2)
    return values


def _load_config(root: Path) -> LibfitsConfig:
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    if sys.version_info >= (3, 11):
        import tomllib

        data = tomllib.loads(text)
        section_raw = data.get("tool", {}).get("pyfits", {}).get("libfits")
        if not isinstance(section_raw, dict):
            msg = "Missing [tool.pyfits.libfits] in pyproject.toml"
            raise SystemExit(msg)
        section = {str(key): str(value) for key, value in section_raw.items()}
    else:
        section = _parse_libfits_section(text)
        if not section:
            msg = "Missing [tool.pyfits.libfits] in pyproject.toml"
            raise SystemExit(msg)

    required = ("repo", "release", "asset", "manifest")
    missing = [key for key in required if key not in section]
    if missing:
        msg = f"[tool.pyfits.libfits] missing keys: {', '.join(missing)}"
        raise SystemExit(msg)
    manifest_sha256_asset = section.get("manifest-sha256-asset", "libfits.a")
    return LibfitsConfig(
        repo=section["repo"],
        release=section["release"],
        asset=section["asset"],
        manifest=section["manifest"],
        manifest_sha256_asset=manifest_sha256_asset,
    )


def _release_url(config: LibfitsConfig, filename: str) -> str:
    return (
        f"https://github.com/{config['repo']}/releases/download/"
        f"{config['release']}/{filename}"
    )


def _download(url: str) -> bytes:
    if not url.startswith("https://"):
        msg = f"Refusing to download non-HTTPS URL: {url}"
        raise SystemExit(msg)
    request = urllib.request.Request(url, headers={"User-Agent": "pyfits-fetch"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except urllib.error.URLError as exc:
        msg = f"Failed to download {url}: {exc}"
        raise SystemExit(msg) from exc


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _bundled_lib_path(root: Path, asset: str) -> Path:
    return root / "src" / "pyfits" / "_lib" / asset


def _stamp_path(dest: Path) -> Path:
    return dest.with_suffix(dest.suffix + ".stamp")


def _lib_env_set() -> bool:
    return bool(os.environ.get("PYFITS_LIB_PATH") or os.environ.get("LIBFITS_LIB_PATH"))


def _read_stamp(stamp: Path) -> dict[str, str] | None:
    if not stamp.is_file():
        return None
    try:
        data = json.loads(stamp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    git_commit = data.get("git_commit")
    manifest_sha256 = data.get("manifest_sha256")
    if not isinstance(git_commit, str) or not isinstance(manifest_sha256, str):
        return None
    return {"git_commit": git_commit, "manifest_sha256": manifest_sha256}


def _write_stamp(stamp: Path, *, git_commit: str | None, manifest_sha256: str) -> None:
    payload = {"git_commit": git_commit, "manifest_sha256": manifest_sha256}
    stamp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _verify_manifest_asset(
    config: LibfitsConfig,
    manifest: dict[str, object],
    *,
    quiet: bool,
) -> str:
    expected_sha = manifest.get("sha256")
    if not isinstance(expected_sha, str) or not expected_sha:
        msg = "manifest.json missing sha256"
        raise SystemExit(msg)

    verify_asset = config["manifest_sha256_asset"]
    verify_url = _release_url(config, verify_asset)
    if not quiet:
        print(f"Verifying release via {verify_url}")
    verify_bytes = _download(verify_url)
    actual_sha = _sha256_hex(verify_bytes)
    if actual_sha != expected_sha:
        msg = (
            f"{verify_asset} sha256 mismatch: expected {expected_sha}, got {actual_sha}"
        )
        raise SystemExit(msg)
    return expected_sha


def ensure_libfits(*, quiet: bool = False) -> Path | None:
    """Ensure bundled libfits.so exists and matches the release manifest.

    The manifest sha256 covers ``manifest-sha256-asset`` (default ``libfits.a``);
    ``libfits.so`` is downloaded from the same release after that check passes.

    Returns:
        Path to the bundled library when fetched or already present, or ``None``
        when ``PYFITS_LIB_PATH`` / ``LIBFITS_LIB_PATH`` is set (fetch skipped).

    Raises:
        SystemExit: When configuration, network, or integrity checks fail.
    """
    if _lib_env_set():
        if not quiet:
            print("PYFITS_LIB_PATH or LIBFITS_LIB_PATH set; skipping libfits download")
        return None

    root = _repo_root()
    config = _load_config(root)
    dest = _bundled_lib_path(root, config["asset"])
    stamp = _stamp_path(dest)

    manifest_bytes = _download(_release_url(config, config["manifest"]))
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    git_commit = manifest.get("git_commit")
    git_commit_str = git_commit if isinstance(git_commit, str) else None

    expected_manifest_sha = manifest.get("sha256")
    if not isinstance(expected_manifest_sha, str) or not expected_manifest_sha:
        msg = "manifest.json missing sha256"
        raise SystemExit(msg)

    stamp_data = _read_stamp(stamp)
    if (
        dest.is_file()
        and stamp_data is not None
        and stamp_data["manifest_sha256"] == expected_manifest_sha
        and stamp_data["git_commit"] == git_commit_str
    ):
        if not quiet:
            print(f"libfits already present at {dest}")
            if git_commit_str:
                print(f"  git_commit={git_commit_str}")
        return dest

    manifest_sha256 = _verify_manifest_asset(config, manifest, quiet=quiet)

    if not quiet:
        print(f"Downloading {_release_url(config, config['asset'])}")
        if git_commit_str:
            print(f"  git_commit={git_commit_str}")

    lib_bytes = _download(_release_url(config, config["asset"]))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=dest.parent,
        delete=False,
        suffix=".tmp",
    ) as tmp:
        tmp.write(lib_bytes)
        tmp_path = Path(tmp.name)
    tmp_path.replace(dest)
    _write_stamp(stamp, git_commit=git_commit_str, manifest_sha256=manifest_sha256)

    if not quiet:
        print(f"Installed libfits to {dest}")
    return dest


def main() -> None:
    """CLI entry point."""
    ensure_libfits()


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        if exc.code:
            sys.exit(exc.code)
