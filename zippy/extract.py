import bz2
import gzip
import lzma
import os
import shutil
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
    external_extract,
    tar_read_mode,
)


logger = get_logger(__name__)


def _extract_with_pyzipper(archive_path, output_path, password, verbose):
    if not pyzipper:
        handle_errors(
            "Archive uses an unsupported ZIP encryption method. Install 'pyzipper' to extract it.",
            verbose,
        )
    if not password:
        handle_errors("Password is required for encrypted ZIP archives.", verbose)
    with pyzipper.AESZipFile(archive_path, "r") as zf:
        zf.pwd = password.encode("utf-8")
        zf.extractall(output_path)


def extract_archive(
    archive_path, output_path=".", password=None, verbose=False, disable_animation=False
):
    """
    Extracts the contents of an archive to the specified output directory.

    Parameters:
    - archive_path (str): Path to the archive file.
    - output_path (str): Directory where the contents will be extracted.
    - password (str): Password for encrypted archives (if applicable).
    - verbose (bool): Enable verbose output for debugging.
    - disable_animation (bool): Disable loading animation.

    Raises:
    - ValueError: If the archive type is unsupported.
    - RuntimeError: If extraction fails due to incorrect password or other issues.
    """
    if not output_path:
        output_path = input(
            "Output directory not provided. Please enter the output directory: "
        )
    archive_type = get_archive_type(archive_path)
    if not archive_type:
        handle_errors(f"Unsupported archive type for: {archive_path}")
    output_path = os.path.abspath(output_path)
    os.makedirs(output_path, exist_ok=True)
    try:
        loading_animation(
            f"Extracting {os.path.basename(archive_path)} to {output_path}",
            duration=2,
            disable_animation=disable_animation,
        )
        if archive_type == "zip":
            try:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(
                        output_path, pwd=password.encode("utf-8") if password else None
                    )
            except RuntimeError as e:
                lower = str(e).lower()
                if "password" in lower:
                    handle_errors("Incorrect password for ZIP archive.", verbose)
                elif "compression method" in lower or "requires" in lower:
                    _extract_with_pyzipper(archive_path, output_path, password, verbose)
                else:
                    handle_errors(f"ZIP Extraction error: {e}", verbose)
            except NotImplementedError:
                _extract_with_pyzipper(archive_path, output_path, password, verbose)
        elif archive_type.startswith("tar"):
            mode = tar_read_mode(archive_type)
            with tarfile.open(archive_path, mode) as tf:
                try:
                    tf.extractall(output_path, filter="data")
                except TypeError:
                    # filter= not supported in Python < 3.12; fall back
                    # to a safe manual extraction routine that rejects path
                    # traversal and link entries.
                    base_output_path = os.path.abspath(output_path)
                    for member in tf.getmembers():
                        member_name = member.name
                        if os.path.isabs(member_name):
                            continue

                        target_path = os.path.abspath(
                            os.path.normpath(os.path.join(base_output_path, member_name))
                        )
                        if (
                            os.path.commonpath([base_output_path, target_path])
                            != base_output_path
                        ):
                            continue

                        if member.issym() or member.islnk():
                            continue

                        if member.isdir():
                            os.makedirs(target_path, exist_ok=True)
                        elif member.isfile():
                            parent_dir = os.path.dirname(target_path)
                            if parent_dir:
                                os.makedirs(parent_dir, exist_ok=True)
                            extracted_file = tf.extractfile(member)
                            if extracted_file is None:
                                continue
                            with extracted_file:
                                with open(target_path, "wb") as outfile:
                                    shutil.copyfileobj(extracted_file, outfile)
                except tarfile.ReadError as e:
                    handle_errors(f"TAR Extraction error: {e}", verbose)
        elif is_single_file_type(archive_type):
            output_file = os.path.join(
                output_path,
                os.path.splitext(os.path.basename(archive_path))[0],
            )
            if archive_type == "gzip":
                opener = gzip.open
                open_kwargs = {}
            elif archive_type == "bz2":
                opener = bz2.open
                open_kwargs = {}
            elif archive_type == "xz":
                opener = lzma.open
                open_kwargs = {"format": lzma.FORMAT_XZ}
            elif archive_type == "lzma":
                opener = lzma.open
                open_kwargs = {"format": lzma.FORMAT_ALONE}
            else:
                handle_errors(
                    f"Extraction for {archive_type} not implemented.", verbose
                )
                return
            with opener(archive_path, "rb", **open_kwargs) as compressed:
                with open(output_file, "wb") as outfile:
                    shutil.copyfileobj(compressed, outfile)
        elif requires_external_tool(archive_type):
            external_extract(archive_path, output_path, verbose=verbose)
        else:
            handle_errors(f"Extraction for {archive_type} not implemented.", verbose)
        logger.info("Successfully extracted to: %s", output_path)
    except Exception as e:
        handle_errors(f"Extraction failed: {e}", verbose)
