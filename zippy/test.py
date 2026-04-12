import bz2
import gzip
import lzma
import os
import tarfile
import zipfile

try:
    import pyzipper
except ImportError:  # pragma: no cover - optional dependency
    pyzipper = None

from .utils import (
    get_logger,
    get_archive_type,
    handle_errors,
    is_single_file_type,
    loading_animation,
    requires_external_tool,
    external_test,
    tar_read_mode,
)


logger = get_logger(__name__)


def _test_zip_with_pyzipper(archive_path, password, verbose):
    if not pyzipper:
        handle_errors(
            "Encrypted ZIP integrity checking requires the 'pyzipper' package.",
            verbose,
        )
    if not password:
        handle_errors("Password is required to test encrypted ZIP archives.", verbose)
    with pyzipper.AESZipFile(archive_path, "r") as zf:
        zf.pwd = password.encode("utf-8")
        for info in zf.infolist():
            if info.is_dir():
                continue
            zf.read(info.filename)
    logger.info("Integrity test for %s: [OK] (AES ZIP)", archive_path)


def test_archive_integrity(
    archive_path, verbose=False, disable_animation=False, password=None
):
    """
    Tests the integrity of an archive.

    Parameters:
    - archive_path (str): Path to the archive file.
    - verbose (bool): Enable verbose output for debugging.
    - disable_animation (bool): Disable loading animation.

    Raises:
    - ValueError: If the archive type is unsupported.
    - RuntimeError: If integrity test fails due to various issues.
    """
    archive_type = get_archive_type(archive_path)
    if not archive_type:
        handle_errors(f"Unsupported archive type for: {archive_path}")
    try:
        loading_animation(
            f"Testing integrity of {os.path.basename(archive_path)}",
            duration=1,
            disable_animation=disable_animation,
        )
        if archive_type == "zip":
            try:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    if password:
                        zf.setpassword(password.encode("utf-8"))
                    result = zf.testzip()
                    if result is None:
                        logger.info("Integrity test for %s: [OK]", archive_path)
                    else:
                        handle_errors(
                            f"Integrity test failed for {archive_path}. Corrupted file: {result}",
                            exit_code=2,
                        )
            except RuntimeError as e:
                lower = str(e).lower()
                if (
                    "password" in lower
                    or "encrypted" in lower
                    or "compression method" in lower
                ):
                    _test_zip_with_pyzipper(archive_path, password, verbose)
                else:
                    handle_errors(
                        f"Integrity test failed for {archive_path}. {e}", exit_code=2
                    )
            except NotImplementedError:
                _test_zip_with_pyzipper(archive_path, password, verbose)
        elif archive_type.startswith("tar"):
            try:
                with tarfile.open(archive_path, tar_read_mode(archive_type)) as tf:
                    members = tf.getmembers()
                    # Read each member to detect data-level corruption
                    for member in members:
                        if member.isfile():
                            f = tf.extractfile(member)
                            if f is not None:
                                with f:
                                    while f.read(8192):
                                        pass
                logger.info(
                    "Integrity test for %s: [OK] (TAR deep check)", archive_path
                )
            except tarfile.ReadError as e:
                handle_errors(
                    f"Integrity test failed for {archive_path}. Possible corruption: {e}",
                    exit_code=2,
                )
        elif is_single_file_type(archive_type):
            try:
                if archive_type == "gzip":
                    opener = gzip.open
                    kwargs = {}
                    error_type = gzip.BadGzipFile
                elif archive_type == "bz2":
                    opener = bz2.open
                    kwargs = {}
                    error_type = OSError
                elif archive_type == "xz":
                    opener = lzma.open
                    kwargs = {"format": lzma.FORMAT_XZ}
                    error_type = lzma.LZMAError
                elif archive_type == "lzma":
                    opener = lzma.open
                    kwargs = {"format": lzma.FORMAT_ALONE}
                    error_type = lzma.LZMAError
                else:
                    handle_errors(
                        f"Integrity test for {archive_type} not implemented.", verbose
                    )
                    return
                with opener(archive_path, "rb", **kwargs) as stream:
                    stream.read(1024)
                logger.info(
                    "Integrity test for %s: [OK] (Basic %s check)",
                    archive_path,
                    archive_type.upper(),
                )
            except error_type as e:  # type: ignore[name-defined]
                handle_errors(
                    f"Integrity test failed for {archive_path}. Possible corruption: {e}",
                    exit_code=2,
                )
        elif requires_external_tool(archive_type):
            external_test(archive_path, verbose=verbose)
            logger.info(
                "Integrity test for %s: [OK] (External backend)", archive_path
            )
        else:
            handle_errors(
                f"Integrity test for {archive_type} not implemented.", verbose
            )
    except Exception as e:
        handle_errors(f"Integrity test could not be performed: {e}", verbose)
