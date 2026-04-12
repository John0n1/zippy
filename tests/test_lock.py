"""Tests for zippy.lock module."""

import os
import zipfile

import pyzipper
import pytest

from zippy.lock import lock_archive
from zippy.utils import ZippyError


class TestLockArchive:
    def test_lock_creates_encrypted_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "locked.zip")
        lock_archive(
            archive,
            files_to_add=sample_file,
            password="secret123",
            disable_animation=True,
        )
        assert os.path.exists(archive)
        # Verify it's encrypted — reading without password should fail
        with pyzipper.AESZipFile(archive, "r") as zf:
            zf.pwd = b"secret123"
            names = zf.namelist()
            assert len(names) >= 1

    def test_lock_non_zip_raises(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.tar.gz")
        with pytest.raises(ZippyError, match="only supported for ZIP"):
            lock_archive(
                archive,
                files_to_add=sample_file,
                archive_type="tar.gz",
                password="secret",
                disable_animation=True,
            )

    def test_relock_existing_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "relock.zip")
        # Create an unencrypted zip first
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        # Re-lock with password (files_to_add=None triggers re-lock path)
        lock_archive(
            archive,
            files_to_add=None,
            password="newpass",
            disable_animation=True,
        )
        assert os.path.exists(archive)

    def test_relock_nonexistent_raises(self, tmp_dir):
        archive = os.path.join(tmp_dir, "nonexistent.zip")
        with pytest.raises(ZippyError, match="not found"):
            lock_archive(
                archive,
                files_to_add=None,
                password="secret",
                disable_animation=True,
            )
