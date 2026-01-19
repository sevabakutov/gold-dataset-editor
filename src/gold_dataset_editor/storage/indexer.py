"""File discovery and indexing for JSONL files."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from gold_dataset_editor.storage.reader import count_entries


@dataclass
class FileInfo:
    """Information about a JSONL file."""

    path: Path
    relative_path: str
    entry_count: int
    last_modified: datetime
    size_bytes: int

    @property
    def display_name(self) -> str:
        """Get a display-friendly name for the file."""
        return self.relative_path


def index_directory(root: Path) -> list[FileInfo]:
    """Recursively discover all JSONL files in a directory.

    Args:
        root: Root directory to search

    Returns:
        List of FileInfo objects sorted by relative path
    """
    root = Path(root).resolve()
    files = []

    for path in root.rglob("*.jsonl"):
        if not path.is_file():
            continue

        stat = path.stat()
        try:
            entry_count = count_entries(path)
        except Exception:
            entry_count = 0

        files.append(
            FileInfo(
                path=path,
                relative_path=str(path.relative_to(root)),
                entry_count=entry_count,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
            )
        )

    # Sort by relative path for consistent ordering
    files.sort(key=lambda f: f.relative_path)
    return files


def get_file_by_id(root: Path, file_id: str, reviewed_root: Path | None = None) -> FileInfo | None:
    """Get FileInfo for a specific file by its ID (relative path).

    Checks reviewed folder first if provided, then falls back to data_root.

    Args:
        root: Root directory (data_root)
        file_id: Relative path of the file (URL-encoded slashes replaced with __)
        reviewed_root: Optional reviewed folder to check first

    Returns:
        FileInfo if found, None otherwise
    """
    root = Path(root).resolve()

    # Decode file_id (replace __ back to /)
    relative_path = file_id.replace("__", "/")

    # Check reviewed folder first if provided
    if reviewed_root:
        reviewed_root = Path(reviewed_root).resolve()
        reviewed_path = reviewed_root / relative_path

        if reviewed_path.exists() and reviewed_path.is_file():
            if not str(reviewed_path.resolve()).startswith(str(reviewed_root)):
                # Security: prevent path traversal
                return None

            stat = reviewed_path.stat()
            try:
                entry_count = count_entries(reviewed_path)
            except Exception:
                entry_count = 0

            return FileInfo(
                path=reviewed_path,
                relative_path=relative_path,
                entry_count=entry_count,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
            )

    # Fall back to data_root
    path = root / relative_path

    if not path.exists() or not path.is_file():
        return None

    if not str(path.resolve()).startswith(str(root)):
        # Security: prevent path traversal
        return None

    stat = path.stat()
    try:
        entry_count = count_entries(path)
    except Exception:
        entry_count = 0

    return FileInfo(
        path=path,
        relative_path=relative_path,
        entry_count=entry_count,
        last_modified=datetime.fromtimestamp(stat.st_mtime),
        size_bytes=stat.st_size,
    )


def path_to_file_id(root: Path, path: Path) -> str:
    """Convert a file path to a file ID.

    Args:
        root: Root directory
        path: Path to the file

    Returns:
        File ID (relative path with / replaced by __)
    """
    relative = str(path.relative_to(root))
    return relative.replace("/", "__")
