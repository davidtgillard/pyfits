"""Shared test helpers."""

from __future__ import annotations

import pytest

from pyfits import FitsError
from pyfits.result import Err, Ok, Result


def unwrap[T](result: Result[T, FitsError]) -> T:
    """Return the success value or fail the test."""
    match result:
        case Ok(value):
            return value
        case Err(error):
            pytest.fail(str(error))
