"""Hatchling build hook: bundled libfits.so makes wheels platform-specific."""

from __future__ import annotations

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomHook(BuildHookInterface):
    """Mark wheels as non-pure so cibuildwheel/auditwheel accept bundled libfits.so."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        if version == "editable":
            return

        build_data["pure_python"] = False
        build_data["infer_tag"] = True

        libfits = Path(self.root) / "src" / "pyfits" / "_lib" / "libfits.so"
        if not libfits.is_file():
            msg = (
                "Missing "
                f"{libfits}; run scripts/fetch_libfits.py before building wheels"
            )
            raise FileNotFoundError(msg)

        force_include = build_data.setdefault("force_include", {})
        if not isinstance(force_include, dict):
            msg = "Unexpected force_include build data"
            raise TypeError(msg)
        force_include[str(libfits.resolve())] = "pyfits/_lib/libfits.so"
