"""Additional validate_response coverage."""

from __future__ import annotations

import pytest

from pyfits._schemas import SchemaId
from pyfits._validate import validate_response
from pyfits.errors import FitsSchemaError
from pyfits.result import Err


def test_validate_response_unknown_operation() -> None:
    with pytest.raises(KeyError, match="unknown operation"):
        validate_response("not_an_operation", {"ok": True})


def test_validate_response_non_validation_schema_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema_err = FitsSchemaError(
        "bad schema",
        operation="schema",
        schema_id=SchemaId.INIT_REQUEST,
    )

    def fake_validate_document(
        _schema_id: SchemaId,
        _doc: dict[str, object],
    ) -> Err[FitsSchemaError]:
        return Err(schema_err)

    monkeypatch.setattr("pyfits._validate.validate_document", fake_validate_document)
    result = validate_response("init", {"ok": True})
    assert isinstance(result, Err)
    assert result.err_value is schema_err
