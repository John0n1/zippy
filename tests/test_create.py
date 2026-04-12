"""Tests for zippy.create module."""

import bz2
import gzip
import lzma
import os
import tarfile
import zipfile

import pytest

from zippy.create import (
    _parse_input_files,
    _sanitize_arcname,
    create_archive,
)
from zippy.utils import ZippyError


class TestParseInputFiles:
    def test_comma_separated_string(self):
        result = _parse_input_files("a.txt, b.txt, c.txt")
        assert result == ["a.txt", "b.txt", "c.txt"]

    def test_list_input(self):
        result = _parse_input_files(["a.txt", "b.txt"])
        assert result == ["a.txt", "b.txt"]

    def test_removes_duplicates(self):
        result = _parse_input_files("a.txt, b.txt, a.txt")
        assert result == ["a.txt", "b.txt"]

    def test_strips_whitespace(self):
        result = _parse_input_files("  a.txt  ,  b.txt  ")
        assert result == ["a.txt", "b.txt"]

    def test_empty_string_raises(self):
        with pytest.raises(ZippyError, match="No files specified"):
            _parse_input_files("")

    def test_invalid_type_raises(self):
        with pytest.raises(ZippyError):
            _parse_input_files(42)


class TestSanitizeArcname:
    def test_relative_path(self):
        result = _sanitize_arcname("docs/file.txt", "/abs/docs/file.txt")
        assert result == "docs/file.txt"

    def test_absolute_path(self):
        result = _sanitize_arcname("/abs/path/file.txt", "/abs/path/file.txt")
        assert result == "file.txt"

    def test_parent_traversal_stripped(self):
        result = _sanitize_arcname("../../file.txt", "/abs/file.txt")
        assert ".." not in result
        assert "file.txt" in result


class TestCreateArchive:
    def test_create_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.zip")
        create_archive(archive, sample_file, "zip", disable_animation=True)
        assert os.path.exists(archive)
        with zipfile.ZipFile(archive, "r") as zf:
            names = zf.namelist()
            assert len(names) >= 1

    def test_create_tar_gz(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.tar.gz")
        create_archive(archive, sample_file, "tar.gz", disable_animation=True)
        assert os.path.exists(archive)
        with tarfile.open(archive, "r:gz") as tf:
            assert len(tf.getnames()) >= 1

    def test_create_tar_bz2(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.tar.bz2")
        create_archive(archive, sample_file, "tar.bz2", disable_animation=True)
        assert os.path.exists(archive)

    def test_create_tar_xz(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.tar.xz")
        create_archive(archive, sample_file, "tar.xz", disable_animation=True)
        assert os.path.exists(archive)

    def test_create_gzip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "sample.gz")
        create_archive(archive, sample_file, "gzip", disable_animation=True)
        assert os.path.exists(archive)
        with gzip.open(archive, "rb") as gf:
            data = gf.read()
            assert b"Hello, Zippy!" in data

    def test_create_bz2(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "sample.bz2")
        create_archive(archive, sample_file, "bz2", disable_animation=True)
        assert os.path.exists(archive)
        with bz2.open(archive, "rb") as bf:
            data = bf.read()
            assert b"Hello, Zippy!" in data

    def test_create_xz(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "sample.xz")
        create_archive(archive, sample_file, "xz", disable_animation=True)
        assert os.path.exists(archive)
        with lzma.open(archive, "rb", format=lzma.FORMAT_XZ) as lf:
            data = lf.read()
            assert b"Hello, Zippy!" in data

    def test_create_lzma(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "sample.lzma")
        create_archive(archive, sample_file, "lzma", disable_animation=True)
        assert os.path.exists(archive)

    def test_create_zip_with_directory(self, sample_dir, tmp_dir):
        archive = os.path.join(tmp_dir, "test_dir.zip")
        create_archive(archive, sample_dir, "zip", disable_animation=True)
        assert os.path.exists(archive)
        with zipfile.ZipFile(archive, "r") as zf:
            names = zf.namelist()
            # Should contain files from subdirectory
            assert any("file1.txt" in n for n in names)
            assert any("file2.txt" in n for n in names)

    def test_create_zip_with_password(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "encrypted.zip")
        create_archive(
            archive, sample_file, "zip", password="secret123", disable_animation=True
        )
        assert os.path.exists(archive)

    def test_create_gzip_multiple_files_raises(self, sample_dir, tmp_dir):
        archive = os.path.join(tmp_dir, "bad.gz")
        # gzip only supports single file; a directory should fail
        with pytest.raises(ZippyError):
            create_archive(archive, sample_dir, "gzip", disable_animation=True)

    def test_infer_archive_type(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "inferred.zip")
        create_archive(archive, sample_file, disable_animation=True)
        assert os.path.exists(archive)

    def test_unknown_type_raises(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.unknown")
        with pytest.raises(ZippyError):
            create_archive(archive, sample_file, disable_animation=True)
