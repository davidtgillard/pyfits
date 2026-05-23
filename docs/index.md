# pyfits

Python bindings for [libfits](https://github.com/davidtgillard/fits) — the fits graph repository engine (nodes, links, registry).

!!! note
    This package is **not** astronomy FITS file I/O (historical Astropy `pyfits`).

## Quick start

```python
from pathlib import Path

from pyfits import Err, ObjectTypeName, Ok, Repo

match Repo.open(Path("my-product")):
    case Ok(repo):
        with repo:
            repo.init()
            repo.register_node_type("req", abstract=True)
            repo.register_node_type("REQ", extends="req")
            match repo.new_node(ObjectTypeName("REQ"), title="First requirement"):
                case Ok(node_id):
                    match repo.validate():
                        case Ok(result):
                            print(result.summary.error_count, len(result.validation_issues))
    case Err(err):
        raise SystemExit(err)
```

Operational methods return `Result[..., FitsError]`. Check `Ok` / `Err` instead of catching exceptions for libfits failures.

## Guides

- [Getting started](getting-started.md) — install pyfits and build libfits
- [Usage](usage.md) — repository workflow and response validation
- [Errors](errors.md) — `Result` and error payload types
- [Threading](threading.md) — session handle rules

## API reference

See the [API Reference](api/index.md) section for auto-generated documentation of all public symbols.
