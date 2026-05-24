"""libfits C ABI and package version (read from the loaded shared library)."""

from __future__ import annotations

from dataclasses import dataclass

from pyfits._native import lib


@dataclass(frozen=True, slots=True, init=False)
class Version:
    """libfits C ABI and package version components.

    Instances are obtained from :func:`get_version` only.

    Attributes:
        major: C struct ABI major version component.
        minor: C struct ABI minor version component.
        patch: C struct ABI patch version component.
        version_string: libfits package version formatted as ``major.minor.patch``.
    """

    major: int
    minor: int
    patch: int

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        msg = "Version cannot be constructed directly; use get_version()"
        raise TypeError(msg)

    @property
    def version_string(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def _make_version(major: int, minor: int, patch: int) -> Version:
    version = object.__new__(Version)
    object.__setattr__(version, "major", major)
    object.__setattr__(version, "minor", minor)
    object.__setattr__(version, "patch", patch)
    return version


def _read_version() -> Version:
    ver = lib().FITS_abi_version()
    return _make_version(
        major=int(ver.major),
        minor=int(ver.minor),
        patch=int(ver.patch),
    )


# contains the version loaded at import time
_VERSION = _read_version()


def get_version() -> Version:
    """Return loaded libfits C ABI and package version.

    Reads ``FITS_abi_version()`` from the libfits shared library loaded at
    import time.

    Returns:
        Loaded libfits version.
    """
    return _VERSION
