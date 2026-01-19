"""Entry CRUD API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from gold_dataset_editor.config import settings
from gold_dataset_editor.models.entry import EntryUpdate, BOOL_SLOTS
from gold_dataset_editor.storage.indexer import get_file_by_id
from gold_dataset_editor.storage.reader import read_jsonl
from gold_dataset_editor.storage.writer import update_entry, write_jsonl_atomic, create_backup, write_reviewed_file, write_working_copy


def _get_reviewed_root():
    """Get the reviewed root directory."""
    return settings.reviewed_output_dir or (settings.data_root.parent / "reviewed")

router = APIRouter()


class EntryResponse(BaseModel):
    """Response for a single entry."""

    index: int
    entry: dict
    has_unsaved: bool = False
    synced_count: int = 0  # Number of other entries updated by role sync


class EntriesListResponse(BaseModel):
    """Response for entry list."""

    entries: list[dict]
    total: int
    page: int
    page_size: int


class SaveResponse(BaseModel):
    """Response for save operation."""

    success: bool
    message: str
    backup_path: str | None = None


@router.get("/{file_id:path}/entries")
async def list_entries(
    file_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    filter_non_null: bool = Query(default=False),
    filter_treatment: bool = Query(default=False),
    filter_bool_slots: bool = Query(default=False),
    filter_qa_hint: bool = Query(default=False),
    search: str = Query(default=""),
) -> EntriesListResponse:
    """List entries for a file with optional filtering and pagination."""
    reviewed_root = _get_reviewed_root()
    file_info = get_file_by_id(settings.data_root, file_id, reviewed_root=reviewed_root)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    all_entries = read_jsonl(file_info.path)

    # Apply filters
    filtered = all_entries
    if filter_non_null:
        filtered = [
            e for e in filtered
            if any(v is not None for v in e.get("gold", {}).get("slots", {}).values())
        ]
    if filter_treatment:
        filtered = [
            e for e in filtered
            if e.get("gold", {}).get("slots", {}).get("treatment") is not None
        ]
    if filter_bool_slots:
        filtered = [
            e for e in filtered
            if any(
                e.get("gold", {}).get("slots", {}).get(slot) is not None
                for slot in BOOL_SLOTS
            )
        ]
    if filter_qa_hint:
        filtered = [e for e in filtered if e.get("qa_hint")]

    if search:
        search_lower = search.lower()
        filtered = [
            e for e in filtered
            if search_lower in _get_searchable_text(e).lower()
        ]

    # Pagination
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_entries = filtered[start:end]

    # Add original indices
    for entry in page_entries:
        entry["_original_index"] = all_entries.index(entry)

    return EntriesListResponse(
        entries=page_entries,
        total=total,
        page=page,
        page_size=page_size,
    )


def _get_message_ts(message: dict | Any) -> int | None:
    """Extract ts_ms from a message if available."""
    if isinstance(message, dict):
        return message.get("ts_ms")
    return None


def _propagate_role_change(
    file_path,
    entries: list[dict],
    edit_session,
    source_index: int,
    ts_ms: int,
    new_role: str,
) -> int:
    """
    Propagate a role change to all entries that contain a message with the given ts_ms.
    Returns the count of other entries that were updated (excluding source_index).
    """
    synced_count = 0

    for idx, disk_entry in enumerate(entries):
        if idx == source_index:
            continue  # Skip the source entry, it's already updated

        # Get entry from session or disk
        entry = edit_session.get_unsaved_entry(file_path, idx)
        if entry is None:
            entry = disk_entry.copy()

        entry_modified = False

        # Check main message
        msg = entry.get("message", {})
        if isinstance(msg, dict) and msg.get("ts_ms") == ts_ms:
            old_role = msg.get("role")
            if old_role != new_role:
                entry["message"]["role"] = new_role
                edit_session.record_change(
                    file_path,
                    idx,
                    entry.get("id", ""),
                    "message.role",
                    old_role,
                    new_role,
                    entry,
                )
                entry_modified = True

        # Check context messages
        context = entry.get("context", [])
        for ctx_idx, ctx_msg in enumerate(context):
            if isinstance(ctx_msg, dict) and ctx_msg.get("ts_ms") == ts_ms:
                old_role = ctx_msg.get("role")
                if old_role != new_role:
                    entry["context"][ctx_idx]["role"] = new_role
                    edit_session.record_change(
                        file_path,
                        idx,
                        entry.get("id", ""),
                        f"context[{ctx_idx}].role",
                        old_role,
                        new_role,
                        entry,
                    )
                    entry_modified = True

        if entry_modified:
            synced_count += 1

    return synced_count


def _get_searchable_text(entry: dict) -> str:
    """Extract searchable text from an entry."""
    parts = []

    # Message text
    message = entry.get("message", {})
    if isinstance(message, dict):
        parts.append(message.get("text", ""))
    else:
        parts.append(str(message))

    # Context messages
    for ctx in entry.get("context", []):
        if isinstance(ctx, dict):
            parts.append(ctx.get("text", ""))

    # Slot values
    slots = entry.get("gold", {}).get("slots", {})
    for v in slots.values():
        if v is not None:
            parts.append(str(v))

    # QA hint
    if entry.get("qa_hint"):
        parts.append(entry["qa_hint"])

    return " ".join(parts)


@router.get("/{file_id:path}/entries/{index}")
async def get_entry(file_id: str, index: int) -> EntryResponse:
    """Get a single entry by index."""
    from gold_dataset_editor.app import edit_session

    reviewed_root = _get_reviewed_root()
    file_info = get_file_by_id(settings.data_root, file_id, reviewed_root=reviewed_root)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    entries = read_jsonl(file_info.path)
    if index < 0 or index >= len(entries):
        raise HTTPException(status_code=404, detail="Entry not found")

    entry = entries[index]
    unsaved = edit_session.get_unsaved_entry(file_info.path, index)
    if unsaved:
        entry = unsaved

    return EntryResponse(
        index=index,
        entry=entry,
        has_unsaved=unsaved is not None,
    )


@router.patch("/{file_id:path}/entries/{index}")
async def patch_entry(file_id: str, index: int, update: EntryUpdate) -> EntryResponse:
    """Update an entry's fields (stores in session, not saved to disk yet)."""
    from gold_dataset_editor.app import edit_session

    reviewed_root = _get_reviewed_root()
    file_info = get_file_by_id(settings.data_root, file_id, reviewed_root=reviewed_root)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    entries = read_jsonl(file_info.path)
    if index < 0 or index >= len(entries):
        raise HTTPException(status_code=404, detail="Entry not found")

    # Get current entry (from session or disk)
    entry = edit_session.get_unsaved_entry(file_info.path, index)
    if entry is None:
        entry = entries[index].copy()

    # Apply updates
    if update.slots is not None:
        if "gold" not in entry:
            entry["gold"] = {}
        if "slots" not in entry["gold"]:
            entry["gold"]["slots"] = {}
        for slot_name, value in update.slots.items():
            # Convert comma-separated string to list for hair_removal_areas
            if slot_name == "hair_removal_areas" and isinstance(value, str) and value:
                value = [v.strip() for v in value.split(",") if v.strip()]
            old_value = entry["gold"]["slots"].get(slot_name)
            entry["gold"]["slots"][slot_name] = value
            edit_session.record_change(
                file_info.path,
                index,
                entry.get("id", ""),
                f"gold.slots.{slot_name}",
                old_value,
                value,
                entry,
            )

    if update.evidence is not None:
        if "gold" not in entry:
            entry["gold"] = {}
        if "evidence" not in entry["gold"]:
            entry["gold"]["evidence"] = {}
        for slot_name, value in update.evidence.items():
            old_value = entry["gold"]["evidence"].get(slot_name)
            entry["gold"]["evidence"][slot_name] = value
            edit_session.record_change(
                file_info.path,
                index,
                entry.get("id", ""),
                f"gold.evidence.{slot_name}",
                old_value,
                value,
                entry,
            )

    if update.intentions is not None:
        if "gold" not in entry:
            entry["gold"] = {}
        old_value = entry["gold"].get("intentions")
        entry["gold"]["intentions"] = update.intentions
        edit_session.record_change(
            file_info.path,
            index,
            entry.get("id", ""),
            "gold.intentions",
            old_value,
            update.intentions,
            entry,
        )

    if update.qa_hint is not None:
        old_value = entry.get("qa_hint")
        entry["qa_hint"] = update.qa_hint
        edit_session.record_change(
            file_info.path,
            index,
            entry.get("id", ""),
            "qa_hint",
            old_value,
            update.qa_hint,
            entry,
        )

    if update.reviewed is not None:
        old_value = entry.get("reviewed", False)
        entry["reviewed"] = update.reviewed
        edit_session.record_change(
            file_info.path,
            index,
            entry.get("id", ""),
            "reviewed",
            old_value,
            update.reviewed,
            entry,
        )

    # Track how many other entries were synced
    synced_count = 0

    if update.message_role is not None:
        if "message" not in entry or not isinstance(entry["message"], dict):
            entry["message"] = {"role": update.message_role, "text": "", "ts_ms": 0}
        old_value = entry["message"].get("role")
        entry["message"]["role"] = update.message_role
        edit_session.record_change(
            file_info.path,
            index,
            entry.get("id", ""),
            "message.role",
            old_value,
            update.message_role,
            entry,
        )
        # Propagate role change to all entries with the same ts_ms
        ts_ms = _get_message_ts(entry["message"])
        if ts_ms is not None:
            synced_count += _propagate_role_change(
                file_info.path,
                entries,
                edit_session,
                index,
                ts_ms,
                update.message_role,
            )

    if update.context_updates is not None:
        for ctx_update in update.context_updates:
            idx = ctx_update.get("index")
            new_role = ctx_update.get("role")
            if idx is not None and new_role and 0 <= idx < len(entry.get("context", [])):
                old_value = entry["context"][idx].get("role")
                entry["context"][idx]["role"] = new_role
                edit_session.record_change(
                    file_info.path,
                    index,
                    entry.get("id", ""),
                    f"context[{idx}].role",
                    old_value,
                    new_role,
                    entry,
                )
                # Propagate role change to all entries with the same ts_ms
                ts_ms = _get_message_ts(entry["context"][idx])
                if ts_ms is not None:
                    synced_count += _propagate_role_change(
                        file_info.path,
                        entries,
                        edit_session,
                        index,
                        ts_ms,
                        new_role,
                    )

    return EntryResponse(
        index=index,
        entry=entry,
        has_unsaved=True,
        synced_count=synced_count,
    )


def _merge_session_entries(file_path, disk_entries: list[dict], edit_session) -> list[dict]:
    """Merge session changes with disk entries.

    Args:
        file_path: Path to the file
        disk_entries: List of entries from disk
        edit_session: The edit session containing unsaved changes

    Returns:
        List of entries with session changes applied
    """
    merged = []
    file_str = str(file_path)
    for idx, disk_entry in enumerate(disk_entries):
        session_entry = edit_session.get_unsaved_entry(file_path, idx)
        if session_entry is not None:
            merged.append(session_entry)
        else:
            merged.append(disk_entry.copy())
    return merged


@router.post("/{file_id:path}/entries/{index}/reviewed")
async def mark_reviewed(file_id: str, index: int) -> EntryResponse:
    """Toggle the reviewed status of an entry."""
    from gold_dataset_editor.app import edit_session
    import logging

    logger = logging.getLogger(__name__)

    reviewed_root = _get_reviewed_root()
    file_info = get_file_by_id(settings.data_root, file_id, reviewed_root=reviewed_root)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    entries = read_jsonl(file_info.path)
    if index < 0 or index >= len(entries):
        raise HTTPException(status_code=404, detail="Entry not found")

    entry = edit_session.get_unsaved_entry(file_info.path, index)
    if entry is None:
        entry = entries[index].copy()

    # Toggle reviewed status
    old_value = entry.get("reviewed", False)
    entry["reviewed"] = not old_value

    edit_session.record_change(
        file_info.path,
        index,
        entry.get("id", ""),
        "reviewed",
        old_value,
        entry["reviewed"],
        entry,
    )

    # Merge session changes and update current entry
    merged_entries = _merge_session_entries(file_info.path, entries, edit_session)
    merged_entries[index] = entry

    # Always save full entries (not cleaned) to reviewed folder for persistence
    try:
        reviewed_path = write_working_copy(
            file_info.path,
            merged_entries,
            settings.data_root,
            settings.reviewed_output_dir,
        )
        edit_session.mark_saved(file_info.path)
        logger.info(f"Saved working copy to: {reviewed_path}")
    except Exception as e:
        logger.error(f"Failed to write working copy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save: {e}")

    return EntryResponse(
        index=index,
        entry=entry,
        has_unsaved=False,
    )


@router.post("/{file_id:path}/save")
async def save_file(file_id: str) -> SaveResponse:
    """Save all unsaved changes for a file to disk."""
    from gold_dataset_editor.app import edit_session

    reviewed_root = _get_reviewed_root()
    file_info = get_file_by_id(settings.data_root, file_id, reviewed_root=reviewed_root)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    if not edit_session.has_unsaved_changes(file_info.path):
        return SaveResponse(
            success=True,
            message="No changes to save",
        )

    # Read current file
    entries = read_jsonl(file_info.path)

    # Apply unsaved changes
    file_str = str(file_info.path)
    for (path_str, idx), modified_entry in edit_session.unsaved_changes.items():
        if path_str == file_str and 0 <= idx < len(entries):
            entries[idx] = modified_entry

    # Save full entries to reviewed folder for persistence
    reviewed_path = write_working_copy(
        file_info.path,
        entries,
        settings.data_root,
        settings.reviewed_output_dir,
    )

    # Mark as saved in session
    edit_session.mark_saved(file_info.path)

    return SaveResponse(
        success=True,
        message=f"Saved {file_info.relative_path}",
        backup_path=str(reviewed_path),
    )


@router.get("/{file_id:path}/search")
async def search_entries(
    file_id: str,
    q: str = Query(..., min_length=1),
) -> EntriesListResponse:
    """Search entries in a file."""
    reviewed_root = _get_reviewed_root()
    file_info = get_file_by_id(settings.data_root, file_id, reviewed_root=reviewed_root)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    all_entries = read_jsonl(file_info.path)
    q_lower = q.lower()

    results = []
    for i, entry in enumerate(all_entries):
        if q_lower in _get_searchable_text(entry).lower():
            entry["_original_index"] = i
            results.append(entry)

    return EntriesListResponse(
        entries=results,
        total=len(results),
        page=1,
        page_size=len(results),
    )
