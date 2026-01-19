"""Tests for JSONL writer."""

import json
import pytest
from pathlib import Path

from gold_dataset_editor.storage.writer import (
    write_jsonl_atomic,
    create_backup,
    update_entry,
    log_edit,
    _compute_changes,
)
from gold_dataset_editor.storage.reader import read_jsonl


class TestWriteJsonlAtomic:
    """Tests for write_jsonl_atomic function."""

    def test_write_jsonl_atomic_creates_file(self, temp_dir):
        """Test that atomic write creates a new file."""
        file_path = temp_dir / "output.jsonl"
        entries = [{"id": "1"}, {"id": "2"}]

        write_jsonl_atomic(file_path, entries)

        assert file_path.exists()
        result = read_jsonl(file_path)
        assert len(result) == 2
        assert result[0]["id"] == "1"

    def test_write_jsonl_atomic_overwrites(self, temp_dir):
        """Test that atomic write overwrites existing file."""
        file_path = temp_dir / "output.jsonl"

        # Write initial content
        write_jsonl_atomic(file_path, [{"id": "old"}])

        # Overwrite
        write_jsonl_atomic(file_path, [{"id": "new"}])

        result = read_jsonl(file_path)
        assert len(result) == 1
        assert result[0]["id"] == "new"

    def test_write_jsonl_atomic_preserves_unicode(self, temp_dir):
        """Test that Unicode characters are preserved."""
        file_path = temp_dir / "unicode.jsonl"
        entries = [{"text": "Привіт, як справи?"}]

        write_jsonl_atomic(file_path, entries)

        result = read_jsonl(file_path)
        assert result[0]["text"] == "Привіт, як справи?"

    def test_write_jsonl_atomic_creates_parent_dirs(self, temp_dir):
        """Test that parent directories are created if needed."""
        file_path = temp_dir / "nested" / "dir" / "output.jsonl"
        entries = [{"id": "1"}]

        write_jsonl_atomic(file_path, entries)

        assert file_path.exists()


class TestCreateBackup:
    """Tests for create_backup function."""

    def test_create_backup_success(self, sample_jsonl_file):
        """Test creating a backup file."""
        backup_path = create_backup(sample_jsonl_file)

        assert backup_path.exists()
        assert ".bak" in backup_path.suffix or backup_path.suffix == ".bak"

        # Verify content is identical
        original = read_jsonl(sample_jsonl_file)
        backup = read_jsonl(backup_path)
        assert original == backup

    def test_create_backup_file_not_found(self, temp_dir):
        """Test backup of non-existent file raises error."""
        file_path = temp_dir / "nonexistent.jsonl"

        with pytest.raises(FileNotFoundError):
            create_backup(file_path)


class TestUpdateEntry:
    """Tests for update_entry function."""

    def test_update_entry_success(self, sample_jsonl_file, temp_dir):
        """Test updating a single entry."""
        entries = read_jsonl(sample_jsonl_file)
        updated = entries[0].copy()
        updated["gold"]["slots"]["name"] = "John"

        update_entry(sample_jsonl_file, 0, updated, backup=False)

        result = read_jsonl(sample_jsonl_file)
        assert result[0]["gold"]["slots"]["name"] == "John"
        # Other entries unchanged
        assert result[1]["gold"]["slots"]["number_phone"] == "+380501234567"

    def test_update_entry_creates_backup(self, sample_jsonl_file, temp_dir):
        """Test that backup is created when requested."""
        original_entries = read_jsonl(sample_jsonl_file)

        entries = read_jsonl(sample_jsonl_file)
        updated = entries[0].copy()
        updated["gold"]["slots"]["name"] = "Jane"

        update_entry(sample_jsonl_file, 0, updated, backup=True)

        # Find backup file
        backup_files = list(sample_jsonl_file.parent.glob("*.bak"))
        assert len(backup_files) >= 1

    def test_update_entry_index_out_of_range(self, sample_jsonl_file):
        """Test updating with invalid index raises error."""
        with pytest.raises(IndexError):
            update_entry(sample_jsonl_file, 100, {"id": "new"}, backup=False)

    def test_update_entry_with_audit_log(self, sample_jsonl_file, temp_dir):
        """Test that edits are logged when log_path is provided."""
        log_path = temp_dir / "edits.log"
        entries = read_jsonl(sample_jsonl_file)
        updated = entries[0].copy()
        updated["gold"]["slots"]["name"] = "Alice"

        update_entry(sample_jsonl_file, 0, updated, backup=False, log_path=log_path)

        assert log_path.exists()
        with open(log_path) as f:
            log_entry = json.loads(f.readline())
            assert log_entry["index"] == 0
            assert "changes" in log_entry


class TestComputeChanges:
    """Tests for _compute_changes helper function."""

    def test_compute_changes_simple(self):
        """Test computing changes between two dicts."""
        old = {"a": 1, "b": 2}
        new = {"a": 1, "b": 3}

        changes = _compute_changes(old, new)

        assert "b" in changes
        assert changes["b"]["old"] == 2
        assert changes["b"]["new"] == 3
        assert "a" not in changes

    def test_compute_changes_nested(self):
        """Test computing changes in nested dicts."""
        old = {"gold": {"slots": {"name": None}}}
        new = {"gold": {"slots": {"name": "John"}}}

        changes = _compute_changes(old, new)

        assert "gold.slots.name" in changes
        assert changes["gold.slots.name"]["old"] is None
        assert changes["gold.slots.name"]["new"] == "John"

    def test_compute_changes_no_changes(self):
        """Test when there are no changes."""
        data = {"a": 1, "b": {"c": 2}}

        changes = _compute_changes(data, data.copy())

        assert changes == {}
