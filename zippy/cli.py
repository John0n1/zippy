import argparse
import json
import os
import sys
from typing import Iterable, Optional

try:
    import readline
except ImportError:  # pragma: no cover - readline not available on Windows
    readline = None

from dotenv import load_dotenv

from . import __version__
from .create import create_archive
from .extract import extract_archive
from .list import list_archive_contents
from .lock import lock_archive
from .repair import repair_archive
from .test import test_archive_integrity
from .unlock import unlock_archive
from .utils import (
    Fore,
    SUPPORTED_ARCHIVE_TYPES,
    ZippyError,
    color_text,
    configure_logging,
    get_logger,
    handle_errors,
    validate_path,
)

SCRIPT_NAME = "zippy"
CONFIG_FILE = "zippy_config.json"
PASSWORD_DICT_DEFAULT = "password_list.txt"


def _format_supported_types() -> str:
    unique_types = sorted({value for value in SUPPORTED_ARCHIVE_TYPES.values()})
    return ", ".join(unique_types)


def display_banner() -> None:
    banner = f"{SCRIPT_NAME.upper()} v{__version__}"
    print(color_text(banner, Fore.CYAN if Fore else None))


def setup_auto_completion(flags: Iterable[str]) -> None:
    if readline is None:  # pragma: no cover
        return

    def completer(text: str, state: int) -> Optional[str]:
        options = [flag for flag in flags if flag.startswith(text)]
        return options[state] if state < len(options) else None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"{SCRIPT_NAME.upper()} - Archive Utility Toolkit",
    )
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument(
        "--extract",
        "-x",
        dest="command",
        action="store_const",
        const="extract",
        help="Extract archive contents",
    )
    command_group.add_argument(
        "--create",
        "-c",
        dest="command",
        action="store_const",
        const="create",
        help="Create a new archive",
    )
    command_group.add_argument(
        "--list",
        "-l",
        dest="command",
        action="store_const",
        const="list",
        help="List archive contents",
    )
    command_group.add_argument(
        "--test",
        "-t",
        dest="command",
        action="store_const",
        const="test",
        help="Test archive integrity",
    )
    command_group.add_argument(
        "--unlock",
        "-u",
        dest="command",
        action="store_const",
        const="unlock",
        help="Attempt to unlock a password-protected ZIP",
    )
    command_group.add_argument(
        "--lock",
        dest="command",
        action="store_const",
        const="lock",
        help="Create or re-lock a password-protected ZIP",
    )
    command_group.add_argument(
        "--repair",
        "-r",
        dest="command",
        action="store_const",
        const="repair",
        help="[Experimental] Attempt archive repair",
    )
    parser.add_argument("archive_file", nargs="?", help="Path to the archive file.")
    parser.add_argument(
        "-o",
        "--output",
        dest="output_path",
        default=".",
        help="Output directory for extraction (default: .)",
    )
    parser.add_argument(
        "-p", "--password", dest="password", help="Password for archive operations"
    )
    parser.add_argument(
        "-d",
        "--dictionary",
        dest="dictionary_file",
        default=PASSWORD_DICT_DEFAULT,
        help=f"Dictionary file for unlock attempts (default: {PASSWORD_DICT_DEFAULT})",
    )
    parser.add_argument(
        "-f",
        "--files",
        dest="files_to_add",
        help="Comma-separated files/directories to add",
    )
    parser.add_argument("--type", dest="archive_type", help="Force archive type")
    parser.add_argument(
        "--repair-mode",
        dest="repair_mode",
        default="remove_corrupted",
        choices=["remove_corrupted", "scan_only"],
        help="Repair mode for ZIP archives",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--no-animation", action="store_true", help="Disable loading animation"
    )
    parser.add_argument(
        "--save-config", dest="save_config_file", help="Save current settings to JSON"
    )
    parser.add_argument(
        "--load-config", dest="load_config_file", help="Load settings from JSON"
    )
    parser.add_argument("--version", action="version", version=f"{SCRIPT_NAME} {__version__}")
    return parser


def _persist_config(args: argparse.Namespace, path: str) -> None:
    data = vars(args).copy()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4)
    get_logger(__name__).info("Configuration saved to %s", path)


def _load_config(path: str) -> dict:
    if not os.path.exists(path):
        handle_errors(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    get_logger(__name__).info("Configuration loaded from %s", path)
    return data


def _apply_loaded_config(args: argparse.Namespace, config: dict) -> None:
    for key, value in config.items():
        if hasattr(args, key):
            setattr(args, key, value)


def _validate_archive_path(command: str, archive_path: Optional[str]) -> None:
    if not archive_path:
        handle_errors("Archive file path is required for this command.")
    if command in {"extract", "list", "test", "unlock", "repair"}:
        validate_path(archive_path, "Archive file path", must_exist=True, is_dir=False)
    elif command in {"create", "lock"}:
        directory = os.path.dirname(os.path.abspath(archive_path)) or "."
        validate_path(directory, "Output directory", must_exist=True, is_dir=True)


def _execute_command(args: argparse.Namespace) -> None:
    command = args.command
    archive_path = args.archive_file
    _validate_archive_path(command, archive_path)

    if command == "extract":
        extract_archive(
            archive_path,
            args.output_path,
            args.password,
            args.verbose,
            args.no_animation,
        )
    elif command == "create":
        create_archive(
            archive_path,
            args.files_to_add,
            args.archive_type,
            args.password,
            args.verbose,
            args.no_animation,
        )
    elif command == "list":
        list_archive_contents(archive_path, args.verbose, args.no_animation)
    elif command == "test":
        test_archive_integrity(
            archive_path, args.verbose, args.no_animation, args.password
        )
    elif command == "unlock":
        unlock_archive(
            archive_path,
            args.dictionary_file,
            args.password,
            args.verbose,
            args.no_animation,
            args.output_path,
        )
    elif command == "lock":
        lock_archive(
            archive_path,
            args.files_to_add,
            "zip",
            args.password,
            args.verbose,
            args.no_animation,
        )
    elif command == "repair":
        repair_archive(
            archive_path,
            args.verbose,
            args.no_animation,
            args.repair_mode,
            args.password,
        )
    else:  # pragma: no cover - defensive
        handle_errors("Invalid command. See 'help'.")


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    command_flags = [
        "--extract",
        "--create",
        "--list",
        "--test",
        "--unlock",
        "--lock",
        "--repair",
    ]
    setup_auto_completion(command_flags)

    if args.save_config_file:
        _persist_config(args, args.save_config_file)
        return 0

    if args.load_config_file:
        config = _load_config(args.load_config_file)
        _apply_loaded_config(args, config)

    display_banner()
    try:
        _execute_command(args)
    except ZippyError as error:
        get_logger(__name__).error(str(error))
        return getattr(error, "exit_code", 1)
    return 0


if __name__ == "__main__":  # pragma: no cover
    try:
        sys.exit(main())
    except ZippyError as error:
        get_logger(__name__).error(str(error))
        sys.exit(getattr(error, "exit_code", 1))
