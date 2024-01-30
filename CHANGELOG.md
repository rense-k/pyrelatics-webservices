# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [x.y.z] - 2024-..-

### Added

- Added testing for Python 3.11 and 3.12, by which they are now supported.
- Added overloads to `RelaticsWebservices.get_result()` and `RelaticsWebservices.run_import()` so linter knows the correct return type.
- Added utility functions to easily travers a path in a Suds object.

### Changed

- Marked type aliases explicit with `TypeAlias`.
- Cleaned up default values for result dataclasses.
- All result dataclasses now use `slots`.

## Fixed

- Fix crash when Import returned a single element.

### Internal

- Upgraded github actions `checkout` to `v4` and `setup-python` to `v5` to support migration to node20.
- Actions only run when a `.py` file is changed.

## [0.2.2] - 2023-02-27

### Changed

- Improves package release script to include `README.md` and `CHANGELOG.md`.

## [0.2.1] - 2023-02-26

### Changed

- Improves package release mechanisme.
- Expanded unit tests.

## [0.2.0] - 2023-02-26

### Added

- Added some first unittests.

### Changed

- `RelaticsWebservices.get_result()` will now return an `ExportResult` object by default, making it similar to
  `run_import()`.

### Removed

- Removed usage of `InvalidOperationError` and `InvalidWorkspaceError` in favor of using `ExportResult` or
  `ImportResult` object to convey the outcome of the request. Both object types have a builtin storage of errors. Both
  will evaluate as Falsy when an error was received, otherwise Truthy.

## [0.1.1] - 2023-02-19

- This release marks the first public release.
