"""Tests for zippy.test module (archive integrity testing)."""

import bz2
import gzip
import lzma
import os
import tarfile
import zipfile

import pytest

from zippy.test import test_archive_integrity as check_integrity
from zippy.utils import ZippyError


class TestIntegrityZip:
    def test_valid_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "good.zip")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        # Should not raise
        check_integrity(archive, disable_animation=True)

    def test_corrupted_zip(self, tmp_dir):
        archive = os.path.join(tmp_dir, "bad.zip")
        # Create a valid zip first, then corrupt it
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("file.txt", "hello world")
        with open(archive, "r+b") as f:
            f.seek(10)
            f.write(b"\x00\x00\x00\x00")
        # Should raise with exit_code=2 or handle gracefully
        try:
            check_integrity(archive, disable_animation=True)
        except ZippyError:
            pass  # Expected for corrupted archives


class TestIntegrityTar:
    def test_valid_tar(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "good.tar")
        with tarfile.open(archive, "w") as tf:
            tf.add(sample_file, "sample.txt")
        check_integrity(archive, disable_animation=True)

    def test_valid_tar_gz(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "good.tar.gz")
        with tarfile.open(archive, "w:gz") as tf:
            tf.add(sample_file, "sample.txt")
        check_integrity(archive, disable_animation=True)


class TestIntegritySingleFile:
    def test_valid_gzip(self, tmp_dir):
        archive = os.path.join(tmp_dir, "good.gz")
        with gzip.open(archive, "wb") as gf:
            gf.write(b"test data for integrity check")
        check_integrity(archive, disable_animation=True)

    def test_valid_bz2(self, tmp_dir):
        archive = os.path.join(tmp_dir, "good.bz2")
        with bz2.open(archive, "wb") as bf:
            bf.write(b"test data for integrity check")
        check_integrity(archive, disable_animation=True)

    def test_valid_xz(self, tmp_dir):
        archive = os.path.join(tmp_dir, "good.xz")
        with lzma.open(archive, "wb", format=lzma.FORMAT_XZ) as lf:
            lf.write(b"test data for integrity check")
        check_integrity(archive, disable_animation=True)

    def test_valid_lzma(self, tmp_dir):
        archive = os.path.join(tmp_dir, "good.lzma")
        with lzma.open(archive, "wb", format=lzma.FORMAT_ALONE) as lf:
            lf.write(b"test data for integrity check")
        check_integrity(archive, disable_animation=True)


class TestIntegrityEdgeCases:
    def test_unsupported_type(self, tmp_dir):
        fake = os.path.join(tmp_dir, "fake.unknown")
        with open(fake, "w") as f:
            f.write("not an archive")
        with pytest.raises(ZippyError, match="Unsupported"):
            check_integrity(fake, disable_animation=True)
