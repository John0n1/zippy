"""Shared fixtures for the zippy test suite."""

import os
import shutil
import tempfile

import pytest


@pytest.fixture
def tmp_dir():
    """Create a temporary directory that is cleaned up after each test."""
    d = tempfile.mkdtemp(prefix="zippy_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_file(tmp_dir):
    """Create a sample text file inside the temporary directory."""
    path = os.path.join(tmp_dir, "sample.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("Hello, Zippy!\nThis is a test file.\n")
    return path


@pytest.fixture
def sample_dir(tmp_dir):
    """Create a sample directory tree for archive creation tests."""
    base = os.path.join(tmp_dir, "sample_dir")
    os.makedirs(os.path.join(base, "subdir"), exist_ok=True)
    with open(os.path.join(base, "file1.txt"), "w") as f:
        f.write("file one content\n")
    with open(os.path.join(base, "subdir", "file2.txt"), "w") as f:
        f.write("file two content\n")
    # Empty directory to test preservation
    os.makedirs(os.path.join(base, "empty_dir"), exist_ok=True)
    return base
