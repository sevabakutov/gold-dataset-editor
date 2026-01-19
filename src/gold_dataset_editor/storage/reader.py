"""JSONL file reader with support for lazy loading."""

import json
from pathlib import Path
from typing import Iterator


def get_source_path(
    original_path: Path,
    data_root: Path,
    reviewed_output_dir: Path | None = None,
) -> Path:
    """Get the path to read from, preferring reviewed version if it exists.

    Args:
        original_path: Path to the original JSONL file in data_root
        data_root: Root directory for JSONL files (output folder)
        reviewed_output_dir: Custom reviewed directory, or None for default

    Returns:
        Path to the reviewed file if it exists, otherwise the original path
    """
    original_path = Path(original_path).resolve()
    data_root = Path(data_root).resolve()

    # Compute reviewed path
    try:
        relative_path = original_path.relative_to(data_root)
    except ValueError:
        # original_path is not under data_root, use just the filename
        relative_path = Path(original_path.name)

    if reviewed_output_dir is not None:
        reviewed_root = Path(reviewed_output_dir).resolve()
    else:
        reviewed_root = data_root.parent / "reviewed"

    reviewed_path = reviewed_root / relative_path

    # Return reviewed path if it exists, otherwise original
    if reviewed_path.exists() and reviewed_path.is_file():
        return reviewed_path
    return original_path


def read_jsonl(path: Path) -> list[dict]:
    """Read all entries from a JSONL file.

    Args:
        path: Path to the JSONL file

    Returns:
        List of dictionaries, one per line

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If a line is not valid JSON
    """
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON on line {line_num}: {e.msg}",
                    e.doc,
                    e.pos,
                )
    return entries


def read_jsonl_lazy(path: Path) -> Iterator[dict]:
    """Lazily read entries from a JSONL file.

    Args:
        path: Path to the JSONL file

    Yields:
        Dictionary for each line in the file

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If a line is not valid JSON
    """
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON on line {line_num}: {e.msg}",
                    e.doc,
                    e.pos,
                )


def read_entry_by_index(path: Path, index: int) -> dict | None:
    """Read a single entry by its index.

    Args:
        path: Path to the JSONL file
        index: Zero-based index of the entry

    Returns:
        The entry dictionary, or None if index is out of range

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the line is not valid JSON
    """
    current = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if current == index:
                return json.loads(line)
            current += 1
    return None


def count_entries(path: Path) -> int:
    """Count the number of entries in a JSONL file.

    Args:
        path: Path to the JSONL file

    Returns:
        Number of non-empty lines in the file
    """
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count
