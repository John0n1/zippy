import bz2
import gzip
import lzma
import os
import posixpath
import shutil
import tarfile
import zipfile

try:
    import pyzipper
except ImportError:  # pragma: no cover - dependency declared; helpful fallback
    pyzipper = None

from .utils import (
    get_logger,
    handle_errors,
    is_single_file_type,
    loading_animation,
    requires_external_tool,
    tar_write_mode,
    validate_path,
    get_archive_type,
)


logger = get_logger(__name__)


def _parse_input_files(files_to_add):
    """Return a list of cleaned input paths."""
    if isinstance(files_to_add, (list, tuple, set)):
        raw_items = [str(item).strip() for item in files_to_add]
    elif isinstance(files_to_add, str):
        raw_items = [segment.strip() for segment in files_to_add.split(",")]
    else:
        handle_errors(
            "Files to add must be provided as a string or iterable of strings."
        )
    cleaned = [item for item in raw_items if item]
    if not cleaned:
        handle_errors("No files specified to add to the archive.")
    # Preserve input order while dropping duplicates.
    return list(dict.fromkeys(cleaned))


def _sanitize_arcname(original_path, absolute_path):
    """Derive a safe archive name based on the provided input path."""
    if os.path.isabs(original_path):
        return os.path.basename(absolute_path).replace(os.sep, "/")
    normalized = os.path.normpath(original_path)
    while normalized.startswith(".." + os.sep):
        normalized = normalized[3:]
    normalized = normalized.lstrip("./")
    sanitized = normalized or os.path.basename(absolute_path)
    return sanitized.replace(os.sep, "/")


def _iter_zip_entries(input_specs):
    """Yield (source_path, arcname) tuples for zip creation."""
    for original_path, absolute_path in input_specs:
        arc_root = _sanitize_arcname(original_path, absolute_path)
        if os.path.isdir(absolute_path):
            # Ensure directory entries exist to preserve empty folders.
            for root, dirs, files in os.walk(absolute_path):
                rel_root = os.path.relpath(root, absolute_path)
                if rel_root == ".":
                    current_arc_root = arc_root
                else:
                    current_arc_root = posixpath.join(
                        arc_root, rel_root.replace(os.sep, "/")
                    )
                yield None, current_arc_root.rstrip("/") + "/"
                if not files and not dirs:
                    continue
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    arcname = posixpath.join(current_arc_root, file_name)
                    yield file_path, arcname
        else:
            yield absolute_path, arc_root


def _collect_input_specs(files_to_add):
    cleaned = _parse_input_files(files_to_add)
    specs = []
    for item in cleaned:
        absolute = validate_path(item, "File to add", must_exist=True)
        specs.append((item, absolute))
    return specs


def _create_archive_internal(
    archive_path, files_to_add, archive_type, password, verbose, disable_animation
):
    """
    Internal function to create an archive with the specified files.

    Parameters:
    - archive_path (str): Path to the output archive file.
    - files_to_add (str): Comma-separated list of files/directories to add to the archive.
    - archive_type (str): Type of the archive (zip, tar, tar.gz, gzip).
    - password (str): Password for encrypted archives (if applicable).
    - verbose (bool): Enable verbose output for debugging.
    - disable_animation (bool): Disable loading animation.

    Raises:
    - ValueError: If no files are specified to add to the archive.
    - RuntimeError: If archive creation fails due to various issues.
    """
    specs = _collect_input_specs(files_to_add)
    if not archive_type:
        archive_type = get_archive_type(archive_path)
        if not archive_type:
            handle_errors(
                "Could not infer archive type from output path. Please specify with --type (zip, tar, tar.gz, tar.bz2, tar.xz, tar.lzma, gzip, bz2, xz, lzma)."
            )
    try:
        loading_animation(
            f"Creating {os.path.basename(archive_path)}",
            duration=2,
            disable_animation=disable_animation,
        )
        if archive_type == "zip":
            pwd = password.encode("utf-8") if password else None
            if pwd:
                if not pyzipper:
                    handle_errors(
                        "Password-protected ZIP creation requires the 'pyzipper' package. "
                        "Install it or omit the password to create an unencrypted archive.",
                        verbose,
                    )
                with pyzipper.AESZipFile(
                    archive_path,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                    encryption=pyzipper.WZ_AES,
                ) as zf:
                    zf.pwd = pwd
                    zf.setencryption(pyzipper.WZ_AES, nbits=256)
                    for source_path, arcname in _iter_zip_entries(specs):
                        if source_path is None:
                            info = zipfile.ZipInfo(
                                arcname if arcname.endswith("/") else arcname + "/"
                            )
                            info.external_attr = 0o755 << 16
                            zf.writestr(info, b"")
                            continue
                        zf.write(source_path, arcname)
            else:
                with zipfile.ZipFile(
                    archive_path, "w", compression=zipfile.ZIP_DEFLATED
                ) as zf:
                    for source_path, arcname in _iter_zip_entries(specs):
                        if source_path is None:
                            info = zipfile.ZipInfo(
                                arcname if arcname.endswith("/") else arcname + "/"
                            )
                            info.external_attr = 0o755 << 16
                            zf.writestr(info, b"")
                            continue
                        zf.write(source_path, arcname=arcname)
        elif archive_type.startswith("tar"):
            mode = tar_write_mode(archive_type)
            if not mode:
                handle_errors(f"Creation for {archive_type} is not supported.")
            with tarfile.open(archive_path, mode) as tf:
                for original_path, absolute_path in specs:
                    arcname = _sanitize_arcname(original_path, absolute_path)
                    tf.add(absolute_path, arcname=arcname)
        elif is_single_file_type(archive_type):
            if len(specs) != 1:
                handle_errors(
                    f"{archive_type} archives can only contain a single file. Please specify one file to compress."
                )
            _, input_file = specs[0]
            if os.path.isdir(input_file):
                handle_errors(
                    f"{archive_type} archives cannot contain directories. Provide a single file."
                )
            with open(input_file, "rb") as infile:
                if archive_type == "gzip":
                    with gzip.open(archive_path, "wb") as gf:
                        shutil.copyfileobj(infile, gf)
                elif archive_type == "bz2":
                    with bz2.open(archive_path, "wb") as bf:
                        shutil.copyfileobj(infile, bf)
                elif archive_type == "xz":
                    with lzma.open(archive_path, "wb", format=lzma.FORMAT_XZ) as lf:
                        shutil.copyfileobj(infile, lf)
                elif archive_type == "lzma":
                    with lzma.open(archive_path, "wb", format=lzma.FORMAT_ALONE) as lf:
                        shutil.copyfileobj(infile, lf)
                else:
                    handle_errors(f"Creation for {archive_type} is not implemented.")
        elif requires_external_tool(archive_type):
            handle_errors(
                f"Creation for {archive_type} archives requires external tooling (patool + backend binaries).",
                verbose,
            )
        else:
            handle_errors(f"Creation for {archive_type} not implemented.", verbose)
        logger.info("Successfully created archive: %s", archive_path)
    except Exception as e:
        handle_errors(f"Archive creation failed: {e}", verbose)


def create_archive(
    archive_path,
    files_to_add,
    archive_type=None,
    password=None,
    verbose=False,
    disable_animation=False,
):
    """
    Creates an archive with the specified files.

    Parameters:
    - archive_path (str): Path to the output archive file.
    - files_to_add (str): Comma-separated list of files/directories to add to the archive.
    - archive_type (str): Type of the archive (zip, tar, tar.gz, gzip).
    - password (str): Password for encrypted archives (if applicable).
    - verbose (bool): Enable verbose output for debugging.
    - disable_animation (bool): Disable loading animation.

    Raises:
    - ValueError: If no files are specified to add to the archive.
    - RuntimeError: If archive creation fails due to various issues.
    """
    if not files_to_add:
        files_to_add = input(
            "Files to add not provided. Please enter the files to add (comma-separated): "
        )
    _create_archive_internal(
        archive_path, files_to_add, archive_type, password, verbose, disable_animation
    )
