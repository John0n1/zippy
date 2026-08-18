import os
import tarfile
import zipfile

from .utils import (
    Fore,
    ZippyError,
    color_text,
    external_list,
    get_archive_type,
    get_logger,
    handle_errors,
    is_single_file_type,
    loading_animation,
    requires_external_tool,
    tar_read_mode,
)

logger = get_logger(__name__)


def list_archive_contents(archive_path, verbose=False, disable_animation=False):
    """
    Lists the contents of an archive.

    Parameters:
    - archive_path (str): Path to the archive file.
    - verbose (bool): Enable verbose output for debugging.
    - disable_animation (bool): Disable loading animation.

    Raises:
    - ValueError: If the archive type is unsupported.
    - RuntimeError: If listing fails due to various issues.
    """
    archive_type = get_archive_type(archive_path)
    if not archive_type:
        handle_errors(f"Unsupported archive type for: {archive_path}")
    try:
        loading_animation(
            f"Listing contents of {os.path.basename(archive_path)}",
            duration=1,
            disable_animation=disable_animation,
        )
        heading = color_text(
            f"\nContents of {archive_path}:\n", Fore.MAGENTA if Fore else None
        )
        print(heading)
        if archive_type == "zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                for name in zf.namelist():
                    print(color_text(name, Fore.GREEN if Fore else None))
        elif archive_type.startswith("tar"):
            mode = tar_read_mode(archive_type)
            with tarfile.open(archive_path, mode) as tf:
                for member in tf.getnames():
                    print(color_text(member, Fore.GREEN if Fore else None))
        elif is_single_file_type(archive_type):
            msg = "Single-file compression detected. Use 'extract' to materialise the payload."
            print(color_text(msg, Fore.YELLOW if Fore else None))
        elif requires_external_tool(archive_type):
            for line in external_list(archive_path, verbose=verbose):
                print(color_text(line, Fore.GREEN if Fore else None))
        else:
            handle_errors(
                f"Listing contents for {archive_type} not implemented.", verbose
            )
    except ZippyError:
        raise
    except Exception as e:
        handle_errors(f"Failed to list archive contents: {e}", verbose)
