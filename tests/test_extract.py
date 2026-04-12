"""Tests for zippy.extract module."""

import bz2
import gzip
import lzma
import os
import tarfile
import zipfile

import pyzipper
import pytest

from zippy.extract import extract_archive
from zippy.utils import ZippyError


class TestExtractZip:
    def test_extract_zip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.zip")
        out_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        extract_archive(archive, out_dir, disable_animation=True)
        assert os.path.exists(os.path.join(out_dir, "sample.txt"))

    def test_extract_zip_with_password(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "encrypted.zip")
        out_dir = os.path.join(tmp_dir, "extracted")
        pwd = "testpass"
        with pyzipper.AESZipFile(
            archive,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zf:
            zf.pwd = pwd.encode("utf-8")
            zf.setencryption(pyzipper.WZ_AES, nbits=256)
            zf.write(sample_file, "sample.txt")
        extract_archive(archive, out_dir, password="testpass", disable_animation=True)
        assert os.path.exists(os.path.join(out_dir, "sample.txt"))


class TestExtractTar:
    @pytest.mark.parametrize(
        "ext,mode",
        [
            (".tar", "w"),
            (".tar.gz", "w:gz"),
            (".tar.bz2", "w:bz2"),
            (".tar.xz", "w:xz"),
        ],
    )
    def test_extract_tar_variants(self, sample_file, tmp_dir, ext, mode):
        archive = os.path.join(tmp_dir, f"test{ext}")
        out_dir = os.path.join(tmp_dir, "extracted")
        with tarfile.open(archive, mode) as tf:
            tf.add(sample_file, "sample.txt")
        extract_archive(archive, out_dir, disable_animation=True)
        assert os.path.exists(os.path.join(out_dir, "sample.txt"))


class TestExtractSingleFile:
    def test_extract_gzip(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "sample.txt.gz")
        out_dir = os.path.join(tmp_dir, "extracted")
        with open(sample_file, "rb") as f_in:
            with gzip.open(archive, "wb") as f_out:
                f_out.write(f_in.read())
        extract_archive(archive, out_dir, disable_animation=True)
        extracted = os.path.join(out_dir, "sample.txt")
        assert os.path.exists(extracted)

    def test_extract_bz2(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "sample.txt.bz2")
        out_dir = os.path.join(tmp_dir, "extracted")
        with open(sample_file, "rb") as f_in:
            with bz2.open(archive, "wb") as f_out:
                f_out.write(f_in.read())
        extract_archive(archive, out_dir, disable_animation=True)

    def test_extract_xz(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "sample.txt.xz")
        out_dir = os.path.join(tmp_dir, "extracted")
        with open(sample_file, "rb") as f_in:
            with lzma.open(archive, "wb", format=lzma.FORMAT_XZ) as f_out:
                f_out.write(f_in.read())
        extract_archive(archive, out_dir, disable_animation=True)

    def test_extract_lzma(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "sample.txt.lzma")
        out_dir = os.path.join(tmp_dir, "extracted")
        with open(sample_file, "rb") as f_in:
            with lzma.open(archive, "wb", format=lzma.FORMAT_ALONE) as f_out:
                f_out.write(f_in.read())
        extract_archive(archive, out_dir, disable_animation=True)


class TestExtractEdgeCases:
    def test_unsupported_type_raises(self, tmp_dir):
        fake = os.path.join(tmp_dir, "fake.unknown")
        with open(fake, "w") as f:
            f.write("not an archive")
        with pytest.raises(ZippyError, match="Unsupported"):
            extract_archive(fake, tmp_dir, disable_animation=True)

    def test_creates_output_dir(self, sample_file, tmp_dir):
        archive = os.path.join(tmp_dir, "test.zip")
        out_dir = os.path.join(tmp_dir, "new_dir", "nested")
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(sample_file, "sample.txt")
        extract_archive(archive, out_dir, disable_animation=True)
        assert os.path.isdir(out_dir)
