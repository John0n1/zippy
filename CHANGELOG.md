# Changelog

## 2.1.0 - 2026-08-19

### Security

- Reject unsafe paths and symbolic links during native ZIP extraction and password recovery.
- Preserve error exit codes instead of wrapping all failures as generic errors.
- Omit passwords and config-control paths from saved JSON configurations.

### Fixed

- Allow `--load-config` to supply the operation and archive path without repeating them on the command line.
- Read compressed streams to EOF during integrity checks so late CRC/truncation failures are detected.
- Ship the starter password dictionary inside wheels and source distributions.
- Replace completed archives and repaired ZIPs atomically.
- Re-lock archives without changing global process working directory.
- Remove the duplicate PyPI publishing workflow.

### Changed

- Add Python 3.9, 3.11, and 3.13 CI plus package validation.
- Clarify authorized recovery, repair limitations, and external-backend trust boundaries.
