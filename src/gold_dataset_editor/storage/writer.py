"""Atomic JSONL writer with backup support and audit logging."""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from gold_dataset_editor.storage.reader import read_jsonl


def write_jsonl_atomic(path: Path, entries: list[dict]) -> None:
    """Write entries to a JSONL file atomically.

    Uses a temporary file and rename to ensure atomicity.
    If the process crashes during write, the original file remains intact.

    Args:
        path: Path to the JSONL file
        entries: List of dictionaries to write
    """
    path = Path(path)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first
    fd, temp_path = tempfile.mkstemp(suffix=".jsonl", dir=parent)
    try:
        with open(fd, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Atomic rename
        shutil.move(temp_path, path)
    except Exception:
        # Clean up temp file on failure
        Path(temp_path).unlink(missing_ok=True)
        raise


def create_backup(path: Path) -> Path:
    """Create a backup of the file.

    Args:
        path: Path to the file to backup

    Returns:
        Path to the backup file
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot backup: {path} does not exist")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".{timestamp}.bak")
    shutil.copy2(path, backup_path)
    return backup_path


def update_entry(
    path: Path,
    index: int,
    entry: dict,
    backup: bool = True,
    log_path: Path | None = None,
) -> None:
    """Update a single entry in a JSONL file.

    Args:
        path: Path to the JSONL file
        index: Zero-based index of the entry to update
        entry: New entry data
        backup: Whether to create a backup before writing
        log_path: Path to audit log file (optional)

    Raises:
        IndexError: If index is out of range
    """
    path = Path(path)
    entries = read_jsonl(path)

    if index < 0 or index >= len(entries):
        raise IndexError(f"Entry index {index} out of range (0-{len(entries) - 1})")

    old_entry = entries[index]

    if backup:
        create_backup(path)

    entries[index] = entry
    write_jsonl_atomic(path, entries)

    # Write to audit log
    if log_path:
        log_edit(log_path, path, index, old_entry, entry)


def log_edit(
    log_path: Path,
    file_path: Path,
    index: int,
    old_entry: dict,
    new_entry: dict,
) -> None:
    """Log an edit to the audit log.

    Args:
        log_path: Path to the audit log file
        file_path: Path to the edited JSONL file
        index: Index of the edited entry
        old_entry: Entry before edit
        new_entry: Entry after edit
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "file": str(file_path),
        "index": index,
        "entry_id": new_entry.get("id", "unknown"),
        "changes": _compute_changes(old_entry, new_entry),
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def _compute_changes(old: dict, new: dict) -> dict[str, Any]:
    """Compute the differences between two entries.

    Returns a dict mapping changed paths to (old_value, new_value) tuples.
    """
    changes = {}

    def compare(path: str, a: Any, b: Any) -> None:
        if isinstance(a, dict) and isinstance(b, dict):
            all_keys = set(a.keys()) | set(b.keys())
            for key in all_keys:
                compare(f"{path}.{key}" if path else key, a.get(key), b.get(key))
        elif a != b:
            changes[path] = {"old": a, "new": b}

    compare("", old, new)
    return changes
