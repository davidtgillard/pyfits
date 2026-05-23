# pyfits

Python bindings for [libfits](https://github.com/davidtgillard/fits) — the fits graph repository engine (nodes, links, registry).

!!! note
    This package is **not** astronomy FITS file I/O (historical Astropy `pyfits`).

## Quick start

```python
from pathlib import Path
from pyfits import ObjectTypeName, Repo

with Repo(Path("my-product")) as repo:
    repo.init()
    repo.register_node_type("req", abstract=True)
    repo.register_node_type("REQ", extends="req")
    node_id = repo.new_node(ObjectTypeName("REQ"), title="First requirement")
    result = repo.validate()
    print(result.summary.error_count, len(result.validation_issues))
```

## Guides

- [Getting started](getting-started.md) — install pyfits and build libfits
- [Usage](usage.md) — repository workflow and response validation
- [Errors](errors.md) — exception types
- [Threading](threading.md) — session handle rules

## API reference

See the [API Reference](api/index.md) section for auto-generated documentation of all public symbols.
