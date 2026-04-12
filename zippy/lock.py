import os
import shutil
import tempfile

from .utils import (
    Fore,
    color_text,
    extract_archive,
    get_logger,
    get_password_interactive,
    handle_errors,
    loading_animation,
    create_archive,
)


logger = get_logger(__name__)


def lock_archive(
    archive_path,
    files_to_add=None,
    archive_type="zip",
    password=None,
    verbose=False,
    disable_animation=False,
):
    """
    Creates a password-protected ZIP archive or re-locks an existing archive with a new password.

    Parameters:
    - archive_path (str): Path to the archive file.
    - files_to_add (str): Comma-separated list of files/directories to add to the archive.
    - archive_type (str): Type of the archive (default: "zip").
    - password (str): Password for the archive.
    - verbose (bool): Enable verbose output for debugging.
    - disable_animation (bool): Disable loading animation.

    Raises:
    - ValueError: If the archive type is unsupported or no files are specified.
    - RuntimeError: If locking fails due to incorrect password or other issues.
    """
    if archive_type != "zip":
        handle_errors(
            "Locking (password protection) is only supported for ZIP archives."
        )
    if not password:
        password = get_password_interactive()
    if files_to_add:
        logger.debug("Locking archive '%s' with provided file list.", archive_path)
        create_archive(
            archive_path,
            files_to_add,
            archive_type,
            password,
            verbose,
            disable_animation,
        )
    else:
        if not os.path.exists(archive_path):
            handle_errors(
                f"Archive file not found: {archive_path}. Cannot lock a non-existent archive."
            )
        # Use absolute path so it remains valid after chdir
        archive_path = os.path.abspath(archive_path)
        temp_dir = tempfile.mkdtemp(prefix="zippy_relock_")
        try:
            loading_animation(
                f"Re-locking {os.path.basename(archive_path)} with password",
                duration=2,
                disable_animation=disable_animation,
            )
            extract_archive(
                archive_path, temp_dir, verbose=verbose, disable_animation=True
            )
            extracted_items = sorted(os.listdir(temp_dir))
            if not extracted_items:
                handle_errors("Extracted archive is empty; nothing to lock.")
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                files_argument = ",".join(extracted_items)
                create_archive(
                    archive_path,
                    files_argument,
                    "zip",
                    password,
                    verbose,
                    disable_animation=True,
                )
            finally:
                os.chdir(original_cwd)
            shutil.rmtree(temp_dir)
            logger.info(
                color_text(
                    f"Successfully re-locked archive: {archive_path} (Password protected)",
                    Fore.GREEN if Fore else None,
                )
            )
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            handle_errors(f"Failed to re-lock archive: {e}", verbose)
