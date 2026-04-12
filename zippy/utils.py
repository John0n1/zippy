import getpass
import io
import itertools
import logging
import os
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

try:
    from colorama import Fore, Style, init as colorama_init
except ImportError:  # pragma: no cover - dependency managed via project metadata
    colorama_init = None
    Fore = Style = None

try:  # pragma: no cover - optional dependency resolved at runtime
    import patoolib
    from patoolib.util import PatoolError
except ImportError:  # pragma: no cover - handled gracefully when invoked
    patoolib = None  # type: ignore[assignment]
    PatoolError = None  # type: ignore[assignment]


LOGGER_NAME = "zippy"
DEFAULT_SPINNER = ["|", "/", "-", "\\"]


class ZippyError(RuntimeError):
    """Custom exception used across the ZIPPY toolkit."""

    def __init__(self, message, exit_code=1):
        super().__init__(message)
        self.exit_code = exit_code


SUPPORTED_ARCHIVE_TYPES = {
    ".zip": "zip",
    ".jar": "zip",
    ".war": "zip",
    ".ear": "zip",
    ".apk": "zip",
    ".ipa": "zip",
    ".tar": "tar",
    ".tar.gz": "tar.gz",
    ".tgz": "tar.gz",
    ".tar.bz2": "tar.bz2",
    ".tbz2": "tar.bz2",
    ".tbz": "tar.bz2",
    ".tar.xz": "tar.xz",
    ".txz": "tar.xz",
    ".tar.lzma": "tar.lzma",
    ".tlz": "tar.lzma",
    ".tar.zst": "tar.zst",
    ".tzst": "tar.zst",
    ".tar.lz": "tar.lz",
    ".tlz4": "tar.lz",
    ".gz": "gzip",
    ".bz2": "bz2",
    ".xz": "xz",
    ".lzma": "lzma",
    ".rar": "rar",
    ".7z": "7z",
    ".zst": "zst",
    ".lz": "lz",
    ".cab": "cab",
    ".iso": "iso",
    ".img": "img",
    ".sit": "sit",
    ".sitx": "sitx",
    ".hqx": "hqx",
    ".arj": "arj",
    ".lzh": "lzh",
    ".lha": "lzh",
    ".ace": "ace",
    ".z": "compress",
    ".Z": "compress",
    ".cpio": "cpio",
    ".deb": "deb",
    ".rpm": "rpm",
    ".pkg": "pkg",
    ".xar": "xar",
    ".appimage": "appimage",
}

TAR_MODE_MAP = {
    "tar": "w",
    "tar.gz": "w:gz",
    "tar.bz2": "w:bz2",
    "tar.xz": "w:xz",
    "tar.lzma": "w:xz",  # Python tarfile uses xz module for lzma streams
}

TAR_READ_MODE_MAP = {
    "tar": "r:",
    "tar.gz": "r:gz",
    "tar.bz2": "r:bz2",
    "tar.xz": "r:xz",
    "tar.lzma": "r:xz",  # Python tarfile uses xz module for lzma streams
}

SINGLE_FILE_COMPRESSORS = {"gzip", "bz2", "xz", "lzma"}


EXTERNAL_ARCHIVE_TYPES = {
    "rar",
    "7z",
    "zst",
    "lz",
    "cab",
    "iso",
    "img",
    "sit",
    "sitx",
    "hqx",
    "arj",
    "lzh",
    "ace",
    "compress",
    "cpio",
    "deb",
    "rpm",
    "pkg",
    "xar",
    "appimage",
    "tar.zst",
    "tar.lz",
}


def tar_write_mode(archive_type):
    return TAR_MODE_MAP.get(archive_type)


def tar_read_mode(archive_type):
    return TAR_READ_MODE_MAP.get(archive_type, "r:*")


def is_single_file_type(archive_type):
    return archive_type in SINGLE_FILE_COMPRESSORS


_COLOR_ENABLED = False


def _init_colors():
    global _COLOR_ENABLED
    if colorama_init is None:
        _COLOR_ENABLED = False
        return
    if not _COLOR_ENABLED:
        colorama_init(autoreset=True)
        _COLOR_ENABLED = sys.stdout.isatty()


def color_text(text, color):
    if not _COLOR_ENABLED or not color:
        return text
    return f"{color}{text}{Style.RESET_ALL}"


def requires_external_tool(archive_type: str) -> bool:
    """Return True when handling the archive type requires patool/third-party tooling."""
    return archive_type in EXTERNAL_ARCHIVE_TYPES


def _ensure_patool_available(archive_type: str):
    if patoolib is None:
        handle_errors(
            f"Support for '{archive_type}' archives requires the optional 'patool' dependency and its backend binaries.")


def external_extract(archive_path: str, output_path: str, verbose: bool = False):
    _ensure_patool_available(get_archive_type(archive_path) or archive_path)
    try:
        patoolib.extract_archive(
            archive_path,
            outdir=output_path,
            verbosity=-1,
        )
    except PatoolError as exc:  # pragma: no cover - delegated to external tools
        handle_errors(f"External extractor failed: {exc}", verbose)


def external_test(archive_path: str, verbose: bool = False):
    _ensure_patool_available(get_archive_type(archive_path) or archive_path)
    try:
        patoolib.test_archive(archive_path, verbosity=-1)
    except PatoolError as exc:  # pragma: no cover
        handle_errors(f"External archive test failed: {exc}", verbose, exit_code=2)


def external_list(archive_path: str, verbose: bool = False):
    _ensure_patool_available(get_archive_type(archive_path) or archive_path)
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            patoolib.list_archive(archive_path, verbosity=-1)
    except PatoolError as exc:  # pragma: no cover
        handle_errors(f"External archive listing failed: {exc}", verbose)
    lines = [line.strip() for line in buffer.getvalue().splitlines() if line.strip()]
    if not lines:
        return ["(no entries reported)"]
    return lines


def get_logger(name=None):
    """Return a module-scoped logger with the project namespace."""
    return logging.getLogger(name or LOGGER_NAME)


def configure_logging(verbose=False):
    """Configure root logging once for the CLI entry point."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(name)s | %(message)s")
    _init_colors()


def loading_animation(message="Processing...", duration=2, disable_animation=False):
    """Display a loading animation while processing."""
    logger = get_logger(__name__)
    if disable_animation or not sys.stdout.isatty():
        logger.info("%s", message)
        return
    spinner = itertools.cycle(DEFAULT_SPINNER)
    end_time = time.time() + duration
    sys.stdout.write(color_text(message + " ", Fore.CYAN if Fore else None))
    sys.stdout.flush()
    while time.time() < end_time:
        frame = next(spinner)
        sys.stdout.write(
            color_text(f"\r{message} {frame}", Fore.CYAN if Fore else None)
        )
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write(
        color_text(f"\r{message} Done!   \n", Fore.GREEN if Fore else None)
    )


def get_archive_type(archive_path, forced_type=None):
    """Determine the archive type from file extension or forced type."""
    if forced_type:
        if forced_type not in set(SUPPORTED_ARCHIVE_TYPES.values()):
            supported = ", ".join(sorted(set(SUPPORTED_ARCHIVE_TYPES.values())))
            raise ValueError(
                f"Invalid archive type specified: {forced_type}. Supported types: {supported}"
            )
        return forced_type

    path = Path(archive_path)
    suffixes = [suffix.lower() for suffix in path.suffixes]
    for length in range(len(suffixes), 0, -1):
        candidate = "".join(suffixes[-length:])
        if candidate in SUPPORTED_ARCHIVE_TYPES:
            return SUPPORTED_ARCHIVE_TYPES[candidate]
    return None


def handle_errors(message, verbose=False, exit_code=1):
    """Handle errors consistently by raising a dedicated exception."""
    logger = get_logger(__name__)
    logger.error(message)
    if verbose:
        import traceback

        traceback.print_exc()
    raise ZippyError(message, exit_code)


def validate_path(path, description="Path", must_exist=True, is_dir=None):
    """Validate and return absolute path."""
    if not path:
        handle_errors(f"{description} cannot be empty.")
    expanded_path = os.path.abspath(os.path.expanduser(os.path.expandvars(path)))
    if must_exist and not os.path.exists(expanded_path):
        handle_errors(f"{description} not found: {path}")
    if is_dir is True and not os.path.isdir(expanded_path):
        handle_errors(f"{description} must be a directory: {path}")
    if is_dir is False and os.path.isdir(expanded_path):
        handle_errors(f"{description} must be a file: {path}")
    return expanded_path


def get_password_interactive(prompt="Enter password: "):
    """Get password input interactively."""
    return getpass.getpass(prompt)


__all__ = [
    "SUPPORTED_ARCHIVE_TYPES",
    "ZippyError",
    "configure_logging",
    "get_logger",
    "color_text",
    "loading_animation",
    "get_archive_type",
    "handle_errors",
    "validate_path",
    "get_password_interactive",
    "tar_write_mode",
    "tar_read_mode",
    "is_single_file_type",
    "requires_external_tool",
    "external_extract",
    "external_test",
    "external_list",
    "Fore",
]


# Salvage functions referenced in repair.py but missing
def _salvage_extract_on_repair_fail(
    archive_path, output_path=".", archive_type=None, verbose=False
):
    """Attempt salvage extraction when repair fails."""
    try:
        logging.info(f"Attempting salvage extraction for {archive_path}...")
        # Import here to avoid circular imports
        from .extract import extract_archive

        extract_archive(
            archive_path, output_path, verbose=verbose, disable_animation=True
        )
        logging.info("Salvage extraction completed successfully.")
        return True
    except Exception as e:
        if verbose:
            logging.info(f"Salvage extraction failed: {e}")
        return False


def _tar_salvage_extraction(archive_path, output_path=".", verbose=False):
    """Attempt salvage extraction for TAR archives."""
    import tarfile

    extracted_count = 0
    try:
        logging.info(f"Attempting TAR salvage extraction for {archive_path}...")
        with tarfile.open(archive_path, "r:*", ignore_zeros=True) as tf:
            for member in tf:
                try:
                    # Prevent path traversal attacks
                    if member.name.startswith("/") or ".." in member.name:
                        if verbose:
                            print(f"Skipping unsafe path: {member.name}")
                        continue
                    tf.extract(member, output_path, filter="data")
                    extracted_count += 1
                except (TypeError, AttributeError):
                    # filter= not supported in older Python; fall back with manual check
                    tf.extract(member, output_path)
                    extracted_count += 1
                except Exception as e:
                    if verbose:
                        print(f"Failed to extract {member.name}: {e}")
                    continue
        print(f"TAR salvage extraction completed. Extracted {extracted_count} files.")
        return extracted_count
    except Exception as e:
        if verbose:
            print(f"TAR salvage extraction failed: {e}")
        return 0


# Functions imported by lock.py - use lazy imports to avoid circular dependencies
def extract_archive(*args, **kwargs):
    """Wrapper for extract_archive to avoid circular imports."""
    from .extract import extract_archive as _extract_archive

    return _extract_archive(*args, **kwargs)


def create_archive(*args, **kwargs):
    """Wrapper for create_archive to avoid circular imports."""
    from .create import create_archive as _create_archive

    return _create_archive(*args, **kwargs)
