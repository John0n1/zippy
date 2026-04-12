"""Tests for zippy.cli module."""

import json
import os
import zipfile

import pytest

from zippy.cli import (
    _apply_loaded_config,
    _format_supported_types,
    _load_config,
    _persist_config,
    build_parser,
    main,
)
from zippy.utils import ZippyError


class TestBuildParser:
    def test_parser_creation(self):
        parser = build_parser()
        assert parser is not None

    def test_extract_command(self):
        parser = build_parser()
        args = parser.parse_args(["--extract", "test.zip"])
        assert args.command == "extract"
        assert args.archive_file == "test.zip"

    def test_create_command(self):
        parser = build_parser()
        args = parser.parse_args(["--create", "test.zip", "-f", "file.txt"])
        assert args.command == "create"
        assert args.files_to_add == "file.txt"

    def test_list_command(self):
        parser = build_parser()
        args = parser.parse_args(["--list", "test.zip"])
        assert args.command == "list"

    def test_test_command(self):
        parser = build_parser()
        args = parser.parse_args(["--test", "test.zip"])
        assert args.command == "test"

    def test_unlock_command(self):
        parser = build_parser()
        args = parser.parse_args(["--unlock", "test.zip"])
        assert args.command == "unlock"

    def test_lock_command(self):
        parser = build_parser()
        args = parser.parse_args(["--lock", "test.zip"])
        assert args.command == "lock"

    def test_repair_command(self):
        parser = build_parser()
        args = parser.parse_args(["--repair", "test.zip"])
        assert args.command == "repair"

    def test_verbose_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--extract", "test.zip", "--verbose"])
        assert args.verbose is True

    def test_no_animation_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--extract", "test.zip", "--no-animation"])
        assert args.no_animation is True

    def test_mutually_exclusive(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--extract", "--create", "test.zip"])

    def test_command_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["test.zip"])

    def test_dictionary_default_is_none(self):
        parser = build_parser()
        args = parser.parse_args(["--unlock", "test.zip"])
        assert args.dictionary_file is None


class TestFormatSupportedTypes:
    def test_returns_string(self):
        result = _format_supported_types()
        assert isinstance(result, str)
        assert "zip" in result


class TestConfigPersistence:
    def test_save_and_load(self, tmp_dir):
        parser = build_parser()
        args = parser.parse_args(["--extract", "test.zip", "--verbose"])
        config_path = os.path.join(tmp_dir, "test_config.json")
        _persist_config(args, config_path)
        assert os.path.exists(config_path)

        loaded = _load_config(config_path)
        assert loaded["command"] == "extract"
        assert loaded["verbose"] is True

    def test_load_nonexistent_raises(self, tmp_dir):
        with pytest.raises(ZippyError, match="not found"):
            _load_config(os.path.join(tmp_dir, "nonexistent.json"))

    def test_apply_config(self):
        parser = build_parser()
        args = parser.parse_args(["--extract", "test.zip"])
        assert args.verbose is False
        _apply_loaded_config(args, {"verbose": True})
        assert args.verbose is True


class TestMainIntegration:
    def test_save_config(self, tmp_dir):
        config_path = os.path.join(tmp_dir, "save_test.json")
        rc = main(["--extract", "test.zip", "--save-config", config_path])
        assert rc == 0
        assert os.path.exists(config_path)

    def test_extract_valid_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.zip")
        out_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        rc = main(["--extract", archive, "-o", out_dir, "--no-animation"])
        assert rc == 0
        assert os.path.exists(os.path.join(out_dir, "sample.txt"))

    def test_list_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.zip")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        rc = main(["--list", archive, "--no-animation"])
        assert rc == 0

    def test_test_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.zip")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        rc = main(["--test", archive, "--no-animation"])
        assert rc == 0

    def test_create_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "created.zip")
        rc = main(["--create", archive, "-f", sample_file, "--no-animation"])
        assert rc == 0
        assert os.path.exists(archive)

    def test_missing_archive_raises(self):
        rc = main(["--extract", "/no/such/file.zip", "--no-animation"])
        assert rc != 0

    def test_load_config_and_execute(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.zip")
        out_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        config_path = os.path.join(tmp_dir, "config.json")
        config = {
            "command": "extract",
            "archive_file": archive,
            "output_path": out_dir,
            "verbose": False,
            "no_animation": True,
        }
        with open(config_path, "w") as f:
            json.dump(config, f)
        rc = main(["--extract", archive, "-o", out_dir, "--load-config", config_path, "--no-animation"])
        assert rc == 0
