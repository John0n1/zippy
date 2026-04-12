import bz2
import gzip
import lzma
import os
import shutil
import zipfile

try:
    import pyzipper
except ImportError:  # pragma: no cover - optional dependency
    pyzipper = None

from .utils import (
    Fore,
    _salvage_extract_on_repair_fail,
    _tar_salvage_extraction,
    color_text,
    get_archive_type,
    get_logger,
    handle_errors,
    loading_animation,
)


logger = get_logger(__name__)


def _open_zip_reader(path, password, verbose):
    if password:
        pwd_bytes = password.encode("utf-8")
        if pyzipper:
            zf = pyzipper.AESZipFile(path, "r")
            zf.pwd = pwd_bytes
            return zf
        reader = zipfile.ZipFile(path, "r")
        reader.setpassword(pwd_bytes)
        return reader
    return zipfile.ZipFile(path, "r")


def _open_zip_writer(path, password):
    if password and pyzipper:
        writer = pyzipper.AESZipFile(
            path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        )
        writer.pwd = password.encode("utf-8")
        writer.setencryption(pyzipper.WZ_AES, nbits=256)
        return writer
    return zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED)


def repair_archive(
    archive_path,
    verbose=False,
    disable_animation=False,
    repair_mode="remove_corrupted",
    password=None,
):
    """
    Repairs a corrupted archive.

    Parameters:
    - archive_path (str): Path to the archive file.
    - verbose (bool): Enable verbose output for debugging.
    - disable_animation (bool): Disable loading animation.
    - repair_mode (str): Repair mode for ZIP archives (default: remove_corrupted).

    Raises:
    - ValueError: If the archive type is unsupported.
    - RuntimeError: If repair fails due to various issues.
    """
    archive_type = get_archive_type(archive_path)
    supported = {
        "zip",
        "tar",
        "tar.gz",
        "tar.bz2",
        "tar.xz",
        "tar.lzma",
        "gzip",
        "bz2",
        "xz",
        "lzma",
    }
    if archive_type not in supported:
        handle_errors(
            "Repair operation is only supported for ZIP, TAR (gz/bz2/xz/lzma) and single-file gzip/bz2/xz/lzma archives at this time."
        )
    logger.warning(
        color_text(
            "[Experimental Feature] Archive repair is a complex process and may not always be successful.",
            Fore.YELLOW if Fore else None,
        )
    )
    logger.info("Repair mode: %s", repair_mode)
    repair_attempted = False
    try:
        loading_animation(
            f"Attempting to repair {os.path.basename(archive_path)}",
            duration=3,
            disable_animation=disable_animation,
        )
        if archive_type == "zip":
            try:
                with _open_zip_reader(archive_path, password, verbose) as zf:
                    bad_file = zf.testzip()
                    if bad_file:
                        logger.warning("Possible corruption detected in: %s", bad_file)
                        if repair_mode == "remove_corrupted":
                            repair_attempted = True
                            logger.info(
                                "Attempting to repair by removing corrupted file: %s",
                                bad_file,
                            )
                            temp_zip_path = archive_path + ".temp_repair.zip"
                            with _open_zip_writer(temp_zip_path, password) as temp_zf:
                                with _open_zip_reader(
                                    archive_path, password, verbose
                                ) as original_zf:
                                    for item in original_zf.infolist():
                                        if item.filename != bad_file:
                                            try:
                                                data = original_zf.read(item.filename)
                                                temp_zf.writestr(item, data)
                                            except Exception as e_read:
                                                logger.warning(
                                                    "Could not copy %s. Error: %s",
                                                    item.filename,
                                                    e_read,
                                                )
                            os.remove(archive_path)
                            os.rename(temp_zip_path, archive_path)
                            logger.info(
                                "Repair finished. Corrupted file '%s' removed. Repaired archive: %s",
                                bad_file,
                                archive_path,
                            )
                        elif repair_mode == "scan_only":
                            logger.info(
                                "Scan-only mode: corruption reported; no changes made."
                            )
                        else:
                            logger.warning(
                                "Unknown repair mode '%s'. No repair action taken.",
                                repair_mode,
                            )
                    else:
                        logger.info(
                            "Integrity check passed for %s. No major errors detected.",
                            archive_path,
                        )
            except zipfile.BadZipFile as e:
                logger.error("ZIP archive appears to be badly corrupted: %s", e)
                logger.error("Specialised ZIP repair tools may be required.")
            except RuntimeError as e:
                if "password" in str(e).lower() or "encrypted" in str(e).lower():
                    handle_errors(
                        "Password is required to repair encrypted ZIP archives.",
                        verbose,
                    )
                else:
                    handle_errors(f"Error during ZIP repair attempt: {e}", verbose)
            except Exception as e:
                handle_errors(f"Error during ZIP repair attempt: {e}", verbose)
        elif archive_type.startswith("tar"):
            repair_attempted = True
            logger.info("Enhanced TAR repair: Attempting to extract readable files...")
            extracted_files_dir = (
                f"{os.path.basename(archive_path)}_extracted_during_repair"
            )
            os.makedirs(extracted_files_dir, exist_ok=True)
            extracted_count = _tar_salvage_extraction(
                archive_path, extracted_files_dir, verbose
            )
            if extracted_count > 0:
                logger.info(
                    "Extracted %s files from TAR archive to: %s",
                    extracted_count,
                    extracted_files_dir,
                )
                logger.warning(
                    "Salvage operation only. Original archive may remain corrupted."
                )
            else:
                logger.warning(
                    "No files could be extracted from the TAR archive. It may be severely corrupted."
                )
        elif archive_type in {"gzip", "bz2", "xz", "lzma"}:
            repair_attempted = True
            logger.info(
                "%s repair: Attempting basic decompression to salvage content...",
                archive_type.upper(),
            )
            output_file_name = (
                f"{os.path.splitext(os.path.basename(archive_path))[0]}_recovered"
            )
            try:
                if archive_type == "gzip":
                    opener = gzip.open
                    kwargs = {}
                elif archive_type == "bz2":
                    opener = bz2.open
                    kwargs = {}
                elif archive_type == "xz":
                    opener = lzma.open
                    kwargs = {"format": lzma.FORMAT_XZ}
                else:  # lzma
                    opener = lzma.open
                    kwargs = {"format": lzma.FORMAT_ALONE}
                with opener(archive_path, "rb", **kwargs) as comp:
                    with open(output_file_name, "wb") as outfile:
                        shutil.copyfileobj(comp, outfile)
                logger.info(
                    "Successfully decompressed content to: %s", output_file_name
                )
            except (gzip.BadGzipFile, OSError, lzma.LZMAError) as e:
                logger.error(
                    "%s archive appears to be corrupted: %s", archive_type.upper(), e
                )
                logger.error("Specialised tools may be required for deeper recovery.")
            except Exception as e:
                handle_errors(
                    f"Error during {archive_type.upper()} repair attempt: {e}", verbose
                )
        logger.info("[Repair attempt finished. Results may vary.]")
        if not repair_attempted and archive_type not in {"gzip", "bz2", "xz", "lzma"}:
            logger.info(
                "No repair action taken based on the integrity check (or in scan_only mode)."
            )
        if repair_attempted or archive_type in {"gzip", "bz2", "xz", "lzma"}:
            salvage_output_dir_name = (
                f"{os.path.basename(archive_path)}_salvaged_content"
            )
            _salvage_extract_on_repair_fail(
                archive_path, salvage_output_dir_name, archive_type, verbose
            )
        logger.warning("It's recommended to have backups of important archives.")
    except Exception as e:
        handle_errors(f"Repair operation failed: {e}", verbose)
