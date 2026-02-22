<div align="center">

# Zippy

<img src="debian/icons/zippy.svg" alt="Zippy" width="125" height="125">

**Version:** `1.0.1`

![PyPi Version](https://img.shields.io/pypi/v/py-zippy?color=blue&logo=python&logoColor=white&style=flat-square)
![Release](https://img.shields.io/github/v/release/John0n1/ZIPPY?color=blue&logo=github&logoColor=white&style=flat-square)

![License](https://img.shields.io/badge/license-MIT-green?style=flat-square&logo=opensourceinitiative&logoColor=white)



### Multi-purpose archive toolkit for creation, extraction, exfiltration, and repair

-> **Supports a wide range of archive formats with a consistent interface.**

-> **Exfiltration by password cracking for encrypted archives.**

-> **Includes a powerful repair toolkit for damaged archives.**

___

### Supported archives

| Format | Algorithm | Deep notes & typical use |
|--------|-----------|---------------------------|
| ZIP (.zip) | DEFLATE (store/deflate/deflate64; variants) | Per-file container with random access and per-file metadata. Widely supported across platforms. Optional password protection (ZipCrypto/AES) depends on tool. Good for cross‑platform distribution and per-file extraction. |
| TAR (.tar) | none (archive only) | Archive container preserving Unix metadata, permissions, and order. Not compressed—commonly paired with compressors (gzip/xz/bzip2) for multi-file archives and backups. |
| TAR.GZ / TGZ (.tar.gz, .tgz) | gzip (DEFLATE) | Stream compressor wrapping tar (single compressed stream). Fast decompression, ubiquitous, not random-access—ideal for streaming and distribution. |
| TAR.BZ2 / TBZ (.tar.bz2, .tbz) | bzip2 | Block compressor with higher ratios for some data at the cost of CPU; slower than gzip, not random-access. Good for distribution when size matters. |
| TAR.XZ / TLZ (.tar.xz, .tlz) | xz / LZMA2 | High compression ratio, memory- and CPU-intensive; slower but yields smaller archives. Best for distribution/releases where size is critical. |
| GZIP (.gz) | gzip (DEFLATE) | Single-file stream compressor. Combine with tar for multi-file archives. Fast and widely supported. |
| BZ2 (.bz2) | bzip2 | Single-file block compressor—better ratios in some cases, slower CPU. Use for single-file compression tasks. |
| XZ (.xz) | xz / LZMA2 | Single-file high-compression format with streaming support; resource-heavy but efficient for size-sensitive workloads. |
| LZMA (.lzma) | LZMA | Older single-file LZMA format similar to xz characteristics; less common but supported for specific compatibility needs. |

</div>

## About
Zippy is a command-line toolkit for working with various archive formats. It provides a consistent interface for creating, extracting, and repairing archives, as well as tools for password cracking on encrypted ZIP files. It works across multiple platforms and is designed for both casual users and professionals needing reliable archive management. The repair tools can help salvage data from corrupted archives, making it a versatile addition to any toolkit. Zippy can also be used in offensive security contexts for penetration testing and forensic analysis. features include:
- **Multi-format support** - handles ZIP (including AES-encrypted), TAR (and compressed variants), and single-file compressors (gzip, bzip2, xz, lzma).
- **Password cracking** - built-in dictionary attack capabilities for encrypted ZIP files using a curated password list.
- **Archive repair** - tools to attempt recovery of corrupted archives, including salvage extraction and best-effort repairs.
- **Cross-platform** - works on Windows, macOS, and Linux with consistent command-line interface.
- **User-friendly features** - progress indicators, colorized logging, and tab completion for ease of use.
- **Automation friendly** - supports configuration saving/loading for repeatable tasks and CI environments.
- **Extensibility** - designed with a modular architecture, allowing for easy integration of new features and support for additional archive formats.
- **Performance** - optimized for speed and efficiency, making it suitable for both small-scale and large-scale archive operations.
- **Security** - incorporates best practices for secure handling of sensitive data, including support for encrypted archives and secure password storage.

## Installation

### From PyPI (recommended)

```bash
python -m pip install py-zippy
```

### From source

```bash
git clone https://github.com/John0n1/ZIPPY.git
cd ZIPPY
python -m pip install .
```

### Debian package

```bash
sudo apt install ./zippy_*.deb
```

## Quick start


### Extract an archive
```bash
zippy --extract backups/site.tar.xz -o ./site
```
### Create a password-protected ZIP from multiple paths
```bash
zippy --lock secure.zip -f docs,images -p "Tru5ted!"
```
### List TAR.BZ2 contents
```bash
zippy --list datasets.tar.bz2
```
### Attempt unlocking with the bundled wordlist
```bash
zippy --unlock encrypted.zip -d password_list.txt --verbose
```
### Run salvage repair on a damaged tarball
```bash
zippy --repair broken.tar.gz --repair-mode remove_corrupted
```
Run `zippy --help` for the full command reference or `zippy --version` to confirm the installed release.

## Configuration & automation

- Use `--save-config <file>` to capture the current flag set (including passwords or dictionary paths if provided).
- Rehydrate saved flags via `--load-config <file>` for repeatable batch jobs.
- Disable animations with `--no-animation` for CI environments.

## Logging & colours

Logging defaults to concise `INFO` output. Add `--verbose` for `DEBUG` traces. Colour output automatically downgrades in non-interactive terminals, while animations fall back to plain log messages when disabled or redirected. Windows terminals are supported through `colorama`.

## Password dictionary

The bundled `password_list.txt` contains hundreds of common credentials, curated for demonstration purposes. The unlock command trims duplicates, ignores comments (`# ...`), and safely handles mixed encodings. Supply your own list with `--dictionary <file>` for larger attacks.

## Contributing
Pull requests are welcome—please open an issue describing the enhancement before submitting substantial changes.

## License

Zippy is released under the MIT License. See `LICENSE` for the full text.

## Disclaimer

Zippy is provided "as is" without warranty of any kind. Use at your own risk and keep backups of critical data.

**The author is not responsible for any data loss or damage resulting from the use of this software.**
