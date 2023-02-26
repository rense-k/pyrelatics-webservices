# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2023-02-26

### Added

- Added some first unittests

### Changed

- `RelaticsWebservices.get_result()` will now return an `ExportResult` object by default, making it similar to
  `run_import()`.

### Removed

- Removed usage of `InvalidOperationError` and `InvalidWorkspaceError` in favor of using `ExportResult` or
  `ImportResult` object to convey the outcome of the request. Both object types have a builtin storage of errors. Both
  will evaluate as Falsy when an error was received, otherwise Truthy.

## [0.1.1] - 2023-02-19

- This release marks the first public release.
