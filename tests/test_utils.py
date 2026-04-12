"""Tests for zippy.utils module."""

import logging
import os

import pytest

from zippy.utils import (
    ZippyError,
    color_text,
    configure_logging,
    get_archive_type,
    get_logger,
    handle_errors,
    is_single_file_type,
    loading_animation,
    requires_external_tool,
    tar_read_mode,
    tar_write_mode,
    validate_path,
)


class TestZippyError:
    def test_default_exit_code(self):
        err = ZippyError("test")
        assert str(err) == "test"
        assert err.exit_code == 1

    def test_custom_exit_code(self):
        err = ZippyError("bad", exit_code=2)
        assert err.exit_code == 2

    def test_is_runtime_error(self):
        assert issubclass(ZippyError, RuntimeError)


class TestGetArchiveType:
    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("test.zip", "zip"),
            ("test.tar", "tar"),
            ("test.tar.gz", "tar.gz"),
            ("test.tgz", "tar.gz"),
            ("test.tar.bz2", "tar.bz2"),
            ("test.tbz2", "tar.bz2"),
            ("test.tar.xz", "tar.xz"),
            ("test.txz", "tar.xz"),
            ("test.tar.lzma", "tar.lzma"),
            ("test.gz", "gzip"),
            ("test.bz2", "bz2"),
            ("test.xz", "xz"),
            ("test.lzma", "lzma"),
            ("test.rar", "rar"),
            ("test.7z", "7z"),
            ("test.jar", "zip"),
            ("test.war", "zip"),
            ("test.apk", "zip"),
            ("test.deb", "deb"),
        ],
    )
    def test_extension_detection(self, filename, expected):
        assert get_archive_type(filename) == expected

    def test_unknown_extension(self):
        assert get_archive_type("test.unknown") is None

    def test_forced_type_valid(self):
        assert get_archive_type("anything.bin", forced_type="zip") == "zip"

    def test_forced_type_invalid(self):
        with pytest.raises(ValueError, match="Invalid archive type"):
            get_archive_type("anything.bin", forced_type="nosuchformat")

    def test_compound_extension(self):
        assert get_archive_type("archive.tar.gz") == "tar.gz"

    def test_case_insensitive(self):
        assert get_archive_type("TEST.ZIP") == "zip"


class TestTarModes:
    def test_write_modes(self):
        assert tar_write_mode("tar") == "w"
        assert tar_write_mode("tar.gz") == "w:gz"
        assert tar_write_mode("tar.bz2") == "w:bz2"
        assert tar_write_mode("tar.xz") == "w:xz"
        assert tar_write_mode("tar.lzma") == "w:xz"

    def test_read_modes(self):
        assert tar_read_mode("tar") == "r:"
        assert tar_read_mode("tar.gz") == "r:gz"
        assert tar_read_mode("tar.bz2") == "r:bz2"
        assert tar_read_mode("tar.xz") == "r:xz"

    def test_unknown_read_mode_fallback(self):
        assert tar_read_mode("tar.unknown") == "r:*"

    def test_unknown_write_mode(self):
        assert tar_write_mode("unknown") is None


class TestIsSingleFileType:
    @pytest.mark.parametrize("t", ["gzip", "bz2", "xz", "lzma"])
    def test_compressors_are_single_file(self, t):
        assert is_single_file_type(t) is True

    @pytest.mark.parametrize("t", ["zip", "tar", "tar.gz", "rar", "7z"])
    def test_non_compressors(self, t):
        assert is_single_file_type(t) is False


class TestRequiresExternalTool:
    @pytest.mark.parametrize("t", ["rar", "7z", "zst", "cab", "iso", "deb", "rpm"])
    def test_external_types(self, t):
        assert requires_external_tool(t) is True

    @pytest.mark.parametrize("t", ["zip", "tar", "tar.gz", "gzip", "bz2"])
    def test_internal_types(self, t):
        assert requires_external_tool(t) is False


class TestValidatePath:
    def test_valid_existing_file(self, sample_file):
        result = validate_path(sample_file, "Test", must_exist=True, is_dir=False)
        assert os.path.isabs(result)

    def test_valid_existing_dir(self, tmp_dir):
        result = validate_path(tmp_dir, "Test", must_exist=True, is_dir=True)
        assert os.path.isabs(result)

    def test_empty_path_raises(self):
        with pytest.raises(ZippyError, match="cannot be empty"):
            validate_path("", "Test")

    def test_nonexistent_raises(self):
        with pytest.raises(ZippyError, match="not found"):
            validate_path("/no/such/path/ever", "Test", must_exist=True)

    def test_file_when_dir_expected(self, sample_file):
        with pytest.raises(ZippyError, match="must be a directory"):
            validate_path(sample_file, "Test", must_exist=True, is_dir=True)

    def test_dir_when_file_expected(self, tmp_dir):
        with pytest.raises(ZippyError, match="must be a file"):
            validate_path(tmp_dir, "Test", must_exist=True, is_dir=False)

    def test_no_existence_check(self, tmp_dir):
        path = os.path.join(tmp_dir, "nonexistent.txt")
        result = validate_path(path, "Test", must_exist=False)
        assert os.path.isabs(result)


class TestHandleErrors:
    def test_raises_zippy_error(self):
        with pytest.raises(ZippyError, match="test error"):
            handle_errors("test error")

    def test_custom_exit_code(self):
        with pytest.raises(ZippyError) as exc_info:
            handle_errors("bad", exit_code=2)
        assert exc_info.value.exit_code == 2


class TestGetLogger:
    def test_returns_logger(self):
        log = get_logger("test_module")
        assert isinstance(log, logging.Logger)

    def test_default_name(self):
        log = get_logger()
        assert log.name == "zippy"


class TestConfigureLogging:
    def test_verbose(self):
        # Reset root logger to allow basicConfig to take effect
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        configure_logging(verbose=True)
        assert root.level <= logging.DEBUG

    def test_non_verbose(self):
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        configure_logging(verbose=False)
        assert root.level <= logging.INFO


class TestColorText:
    def test_no_color(self):
        assert color_text("hello", None) == "hello"

    def test_disabled_color(self):
        # color_text returns plain text when _COLOR_ENABLED is False
        result = color_text("hello", "FAKE_COLOR")
        assert "hello" in result


class TestLoadingAnimation:
    def test_disabled_animation(self):
        # Should not raise and should complete quickly
        loading_animation("test", duration=0.1, disable_animation=True)

    def test_non_tty(self):
        # In test environment stdout is not a tty, so animation should be skipped
        loading_animation("test", duration=0.1, disable_animation=False)
