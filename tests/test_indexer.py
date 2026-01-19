"""Tests for file indexer."""

import json
import pytest
from pathlib import Path

from gold_dataset_editor.storage.indexer import (
    index_directory,
    get_file_by_id,
    path_to_file_id,
    FileInfo,
)


class TestIndexDirectory:
    """Tests for index_directory function."""

    def test_index_directory_finds_files(self, temp_dir, sample_jsonl_file):
        """Test that indexer finds JSONL files."""
        files = index_directory(temp_dir)

        assert len(files) == 1
        assert files[0].relative_path == "test.jsonl"
        assert files[0].entry_count == 3

    def test_index_directory_recursive(self, temp_dir):
        """Test that indexer finds files in subdirectories."""
        # Create nested structure
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        file1 = temp_dir / "file1.jsonl"
        file2 = subdir / "file2.jsonl"

        for f in [file1, file2]:
            with open(f, "w") as fp:
                fp.write('{"id": "test"}\n')

        files = index_directory(temp_dir)

        assert len(files) == 2
        paths = {f.relative_path for f in files}
        assert "file1.jsonl" in paths
        assert "subdir/file2.jsonl" in paths

    def test_index_directory_ignores_non_jsonl(self, temp_dir):
        """Test that non-JSONL files are ignored."""
        (temp_dir / "file.txt").touch()
        (temp_dir / "file.json").touch()
        (temp_dir / "file.jsonl").write_text('{"id": "test"}\n')

        files = index_directory(temp_dir)

        assert len(files) == 1
        assert files[0].relative_path == "file.jsonl"

    def test_index_directory_sorted_by_path(self, temp_dir):
        """Test that results are sorted by relative path."""
        for name in ["c.jsonl", "a.jsonl", "b.jsonl"]:
            (temp_dir / name).write_text('{"id": "test"}\n')

        files = index_directory(temp_dir)

        paths = [f.relative_path for f in files]
        assert paths == ["a.jsonl", "b.jsonl", "c.jsonl"]

    def test_index_directory_empty(self, temp_dir):
        """Test indexing an empty directory."""
        files = index_directory(temp_dir)
        assert files == []


class TestGetFileById:
    """Tests for get_file_by_id function."""

    def test_get_file_by_id_success(self, temp_dir, sample_jsonl_file):
        """Test getting file info by ID."""
        file_id = "test.jsonl"
        file_info = get_file_by_id(temp_dir, file_id)

        assert file_info is not None
        assert file_info.relative_path == "test.jsonl"
        assert file_info.entry_count == 3

    def test_get_file_by_id_nested(self, temp_dir):
        """Test getting nested file with encoded path."""
        subdir = temp_dir / "nested" / "dir"
        subdir.mkdir(parents=True)
        file_path = subdir / "test.jsonl"
        file_path.write_text('{"id": "test"}\n')

        # ID uses __ as path separator
        file_id = "nested__dir__test.jsonl"
        file_info = get_file_by_id(temp_dir, file_id)

        assert file_info is not None
        assert file_info.relative_path == "nested/dir/test.jsonl"

    def test_get_file_by_id_not_found(self, temp_dir):
        """Test getting non-existent file returns None."""
        file_info = get_file_by_id(temp_dir, "nonexistent.jsonl")
        assert file_info is None

    def test_get_file_by_id_prevents_traversal(self, temp_dir):
        """Test that path traversal is prevented."""
        # Try to escape the root directory
        file_info = get_file_by_id(temp_dir, "..__outside.jsonl")
        assert file_info is None


class TestPathToFileId:
    """Tests for path_to_file_id function."""

    def test_path_to_file_id_simple(self, temp_dir):
        """Test converting simple path to ID."""
        file_path = temp_dir / "test.jsonl"
        file_id = path_to_file_id(temp_dir, file_path)
        assert file_id == "test.jsonl"

    def test_path_to_file_id_nested(self, temp_dir):
        """Test converting nested path to ID."""
        file_path = temp_dir / "sub" / "dir" / "test.jsonl"
        file_id = path_to_file_id(temp_dir, file_path)
        assert file_id == "sub__dir__test.jsonl"


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_file_info_display_name(self, temp_dir):
        """Test FileInfo display_name property."""
        info = FileInfo(
            path=temp_dir / "test.jsonl",
            relative_path="subdir/test.jsonl",
            entry_count=10,
            last_modified=None,
            size_bytes=100,
        )

        assert info.display_name == "subdir/test.jsonl"
