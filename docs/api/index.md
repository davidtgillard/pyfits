# API overview

Public exports from the `pyfits` package:

::: pyfits
    options:
      show_root_heading: false
      heading_level: 3
      members:
        - Repo
        - ValidateResult
        - ValidateSummary
        - ValidationIssue
        - FitsError
        - FitsSchemaError
        - FitsStatus
        - __version__
        - libfits_version_major
        - api_version_minor
        - libfits_version_packed
        - libfits_version_string
        - lib_path
      show_submodules: false

## Submodules

- [`Repo`](repo.md) — repository session API
- [`Models`](models.md) — validation result types
- [`Exceptions`](exceptions.md) — error types and status codes
- [`Schemas`](schemas.md) — JSON Schema access helpers
