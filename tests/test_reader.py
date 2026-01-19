"""Tests for JSONL reader."""

import json
import pytest
from pathlib import Path

from gold_dataset_editor.storage.reader import (
    read_jsonl,
    read_jsonl_lazy,
    read_entry_by_index,
    count_entries,
)


class TestReadJsonl:
    """Tests for read_jsonl function."""

    def test_read_jsonl_success(self, sample_jsonl_file):
        """Test reading a valid JSONL file."""
        entries = read_jsonl(sample_jsonl_file)
        assert len(entries) == 3
        assert entries[0]["id"] == "test_message.json:0"
        assert entries[1]["gold"]["slots"]["number_phone"] == "+380501234567"
        assert entries[2]["gold"]["slots"]["location"] == "Kyiv"

    def test_read_jsonl_preserves_all_fields(self, temp_dir):
        """Test that extra fields are preserved."""
        file_path = temp_dir / "extra_fields.jsonl"
        entry = {
            "id": "test",
            "custom_field": "custom_value",
            "nested": {"a": 1, "b": 2}
        }
        with open(file_path, "w") as f:
            f.write(json.dumps(entry) + "\n")

        entries = read_jsonl(file_path)
        assert len(entries) == 1
        assert entries[0]["custom_field"] == "custom_value"
        assert entries[0]["nested"]["a"] == 1

    def test_read_jsonl_empty_file(self, temp_dir):
        """Test reading an empty file."""
        file_path = temp_dir / "empty.jsonl"
        file_path.touch()

        entries = read_jsonl(file_path)
        assert entries == []

    def test_read_jsonl_file_not_found(self, temp_dir):
        """Test reading a non-existent file."""
        file_path = temp_dir / "nonexistent.jsonl"
        with pytest.raises(FileNotFoundError):
            read_jsonl(file_path)

    def test_read_jsonl_invalid_json(self, temp_dir):
        """Test reading a file with invalid JSON."""
        file_path = temp_dir / "invalid.jsonl"
        with open(file_path, "w") as f:
            f.write('{"valid": true}\n')
            f.write('not valid json\n')

        with pytest.raises(json.JSONDecodeError):
            read_jsonl(file_path)

    def test_read_jsonl_skips_empty_lines(self, temp_dir):
        """Test that empty lines are skipped."""
        file_path = temp_dir / "with_empty.jsonl"
        with open(file_path, "w") as f:
            f.write('{"id": "1"}\n')
            f.write('\n')
            f.write('{"id": "2"}\n')
            f.write('   \n')
            f.write('{"id": "3"}\n')

        entries = read_jsonl(file_path)
        assert len(entries) == 3


class TestReadJsonlLazy:
    """Tests for read_jsonl_lazy function."""

    def test_lazy_read_yields_entries(self, sample_jsonl_file):
        """Test that lazy reading yields entries one by one."""
        entries = list(read_jsonl_lazy(sample_jsonl_file))
        assert len(entries) == 3
        assert entries[0]["id"] == "test_message.json:0"

    def test_lazy_read_is_iterator(self, sample_jsonl_file):
        """Test that lazy read returns an iterator."""
        result = read_jsonl_lazy(sample_jsonl_file)
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')


class TestReadEntryByIndex:
    """Tests for read_entry_by_index function."""

    def test_read_entry_by_index_first(self, sample_jsonl_file):
        """Test reading the first entry."""
        entry = read_entry_by_index(sample_jsonl_file, 0)
        assert entry is not None
        assert entry["id"] == "test_message.json:0"

    def test_read_entry_by_index_middle(self, sample_jsonl_file):
        """Test reading a middle entry."""
        entry = read_entry_by_index(sample_jsonl_file, 1)
        assert entry is not None
        assert entry["gold"]["slots"]["number_phone"] == "+380501234567"

    def test_read_entry_by_index_last(self, sample_jsonl_file):
        """Test reading the last entry."""
        entry = read_entry_by_index(sample_jsonl_file, 2)
        assert entry is not None
        assert entry["gold"]["slots"]["location"] == "Kyiv"

    def test_read_entry_by_index_out_of_range(self, sample_jsonl_file):
        """Test reading an entry that doesn't exist."""
        entry = read_entry_by_index(sample_jsonl_file, 100)
        assert entry is None

    def test_read_entry_by_index_negative(self, sample_jsonl_file):
        """Test reading with negative index returns None."""
        entry = read_entry_by_index(sample_jsonl_file, -1)
        assert entry is None


class TestCountEntries:
    """Tests for count_entries function."""

    def test_count_entries(self, sample_jsonl_file):
        """Test counting entries in a file."""
        count = count_entries(sample_jsonl_file)
        assert count == 3

    def test_count_entries_empty_file(self, temp_dir):
        """Test counting entries in an empty file."""
        file_path = temp_dir / "empty.jsonl"
        file_path.touch()

        count = count_entries(file_path)
        assert count == 0
