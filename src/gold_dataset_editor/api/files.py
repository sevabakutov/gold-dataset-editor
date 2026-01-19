"""File list API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gold_dataset_editor.config import settings
from gold_dataset_editor.storage.indexer import index_directory, get_file_by_id

router = APIRouter()


def _get_reviewed_root():
    """Get the reviewed root directory."""
    return settings.reviewed_output_dir or (settings.data_root.parent / "reviewed")


class FileStats(BaseModel):
    """Statistics for a single file."""

    path: str
    entry_count: int
    reviewed_count: int
    non_null_slots_count: int
    last_modified: str


class FileListResponse(BaseModel):
    """Response for file list endpoint."""

    files: list[dict]
    total_files: int
    total_entries: int


@router.get("")
async def list_files() -> FileListResponse:
    """List all JSONL files in the data root."""
    file_list = index_directory(settings.data_root)

    return FileListResponse(
        files=[
            {
                "id": f.relative_path.replace("/", "__"),
                "path": f.relative_path,
                "entry_count": f.entry_count,
                "last_modified": f.last_modified.isoformat(),
                "size_bytes": f.size_bytes,
            }
            for f in file_list
        ],
        total_files=len(file_list),
        total_entries=sum(f.entry_count for f in file_list),
    )


@router.get("/{file_id:path}/stats")
async def get_file_stats(file_id: str) -> FileStats:
    """Get statistics for a specific file."""
    from gold_dataset_editor.storage.reader import read_jsonl

    reviewed_root = _get_reviewed_root()
    file_info = get_file_by_id(settings.data_root, file_id, reviewed_root=reviewed_root)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    entries = read_jsonl(file_info.path)

    # Count reviewed entries
    reviewed_count = sum(1 for e in entries if e.get("reviewed", False))

    # Count entries with any non-null slot
    non_null_count = 0
    for entry in entries:
        gold = entry.get("gold", {})
        slots = gold.get("slots", {})
        if any(v is not None for v in slots.values()):
            non_null_count += 1

    return FileStats(
        path=file_info.relative_path,
        entry_count=file_info.entry_count,
        reviewed_count=reviewed_count,
        non_null_slots_count=non_null_count,
        last_modified=file_info.last_modified.isoformat(),
    )
