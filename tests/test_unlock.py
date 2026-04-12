"""Tests for zippy.unlock module."""

import os
import zipfile

import pyzipper
import pytest

from zippy.unlock import unlock_archive
from zippy.utils import ZippyError


class TestUnlockArchive:
    def _create_encrypted_zip(self, archive_path, password, content="secret data"):
        with pyzipper.AESZipFile(
            archive_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zf:
            zf.pwd = password.encode("utf-8")
            zf.setencryption(pyzipper.WZ_AES, nbits=256)
            zf.writestr("secret.txt", content.encode("utf-8"))

    def test_unlock_with_correct_password(self, tmp_dir):
        archive = os.path.join(tmp_dir, "locked.zip")
        out_dir = os.path.join(tmp_dir, "unlocked")
        self._create_encrypted_zip(archive, "password123")
        unlock_archive(
            archive,
            password="password123",
            disable_animation=True,
            output_path=out_dir,
        )
        assert os.path.exists(os.path.join(out_dir, "secret.txt"))

    def test_unlock_with_dictionary(self, tmp_dir):
        archive = os.path.join(tmp_dir, "locked.zip")
        out_dir = os.path.join(tmp_dir, "unlocked")
        self._create_encrypted_zip(archive, "letmein")
        # Create a small dictionary
        dict_file = os.path.join(tmp_dir, "dict.txt")
        with open(dict_file, "w") as f:
            f.write("wrongpass\n")
            f.write("# comment line\n")
            f.write("letmein\n")
            f.write("anotherpass\n")
        unlock_archive(
            archive,
            dictionary_file=dict_file,
            disable_animation=True,
            output_path=out_dir,
        )
        assert os.path.exists(os.path.join(out_dir, "secret.txt"))

    def test_unlock_non_zip_raises(self, tmp_dir):
        fake = os.path.join(tmp_dir, "fake.tar.gz")
        with open(fake, "wb") as f:
            f.write(b"\x1f\x8b" + b"\x00" * 20)  # minimal gzip header
        with pytest.raises(ZippyError, match="only supported for ZIP"):
            unlock_archive(fake, disable_animation=True)

    def test_unlock_extracts_to_output_path(self, tmp_dir):
        """Verify unlock extracts to the specified output_path, not CWD."""
        archive = os.path.join(tmp_dir, "locked.zip")
        out_dir = os.path.join(tmp_dir, "custom_output")
        self._create_encrypted_zip(archive, "test")
        unlock_archive(
            archive,
            password="test",
            disable_animation=True,
            output_path=out_dir,
        )
        assert os.path.isdir(out_dir)
        assert os.path.exists(os.path.join(out_dir, "secret.txt"))

    def test_unlock_password_only_no_dict_needed(self, tmp_dir):
        """When --password is given, no dictionary file should be required."""
        archive = os.path.join(tmp_dir, "locked.zip")
        out_dir = os.path.join(tmp_dir, "unlocked")
        self._create_encrypted_zip(archive, "mypass")
        # dictionary_file=None should not cause failure when password is given
        unlock_archive(
            archive,
            dictionary_file=None,
            password="mypass",
            disable_animation=True,
            output_path=out_dir,
        )
        assert os.path.exists(os.path.join(out_dir, "secret.txt"))
