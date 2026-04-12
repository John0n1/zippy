"""Tests for zippy.repair module."""

import gzip
import os
import tarfile
import zipfile

import pytest

from zippy.repair import repair_archive
from zippy.utils import ZippyError


class TestRepairZip:
    def test_repair_valid_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "good.zip")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        # Should not raise — no corruption found
        repair_archive(archive, disable_animation=True)

    def test_repair_scan_only(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "good.zip")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        repair_archive(archive, disable_animation=True, repair_mode="scan_only")

    def test_repair_badly_corrupted_zip(self, tmp_dir):
        archive = os.path.join(tmp_dir, "bad.zip")
        with open(archive, "wb") as f:
            f.write(b"PK\x03\x04" + b"\x00" * 100)
        # Should handle gracefully
        try:
            repair_archive(archive, disable_animation=True)
        except ZippyError:
            pass


class TestRepairTar:
    def test_repair_tar(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "good.tar")
        with tarfile.open(archive, "w") as tf:
            tf.add(sample_file, "sample.txt")
        # Change to tmp_dir to avoid creating salvage dirs in CWD
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            repair_archive(archive, disable_animation=True)
        finally:
            os.chdir(original_cwd)


class TestRepairSingleFile:
    def test_repair_gzip(self, tmp_dir):
        archive = os.path.join(tmp_dir, "test.gz")
        with gzip.open(archive, "wb") as gf:
            gf.write(b"test data")
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            repair_archive(archive, disable_animation=True)
        finally:
            os.chdir(original_cwd)


class TestRepairEdgeCases:
    def test_unsupported_type(self, tmp_dir):
        fake = os.path.join(tmp_dir, "fake.rar")
        with open(fake, "w") as f:
            f.write("fake")
        with pytest.raises(ZippyError, match="only supported"):
            repair_archive(fake, disable_animation=True)
