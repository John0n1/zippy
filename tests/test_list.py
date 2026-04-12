"""Tests for zippy.list module."""

import os
import tarfile
import zipfile

import pytest

from zippy.list import list_archive_contents
from zippy.utils import ZippyError


class TestListArchiveContents:
    def test_list_zip(self, sample_file, tmp_dir, capsys):
        archive = os.path.join(tmp_dir, "test.zip")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
            zf.write(sample_file, "other.txt")
        list_archive_contents(archive, disable_animation=True)
        captured = capsys.readouterr()
        assert "sample.txt" in captured.out
        assert "other.txt" in captured.out

    def test_list_tar(self, sample_file, tmp_dir, capsys):
        archive = os.path.join(tmp_dir, "test.tar")
        with tarfile.open(archive, "w") as tf:
            tf.add(sample_file, "sample.txt")
        list_archive_contents(archive, disable_animation=True)
        captured = capsys.readouterr()
        assert "sample.txt" in captured.out

    def test_list_single_file(self, tmp_dir, capsys):
        import gzip

        archive = os.path.join(tmp_dir, "test.gz")
        with gzip.open(archive, "wb") as gf:
            gf.write(b"data")
        list_archive_contents(archive, disable_animation=True)
        captured = capsys.readouterr()
        assert "Single-file compression" in captured.out

    def test_list_unsupported(self, tmp_dir):
        fake = os.path.join(tmp_dir, "fake.unknown")
        with open(fake, "w") as f:
            f.write("not an archive")
        with pytest.raises(ZippyError, match="Unsupported"):
            list_archive_contents(fake, disable_animation=True)
