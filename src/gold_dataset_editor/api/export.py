"""Export and reporting API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from gold_dataset_editor.config import settings
from gold_dataset_editor.storage.indexer import index_directory
from gold_dataset_editor.storage.reader import read_jsonl
from gold_dataset_editor.models.entry import ALL_SLOTS, BOOL_SLOTS

router = APIRouter()


class SlotStats(BaseModel):
    """Statistics for a single slot."""

    total_non_null: int
    true_count: int = 0  # For bool slots
    false_count: int = 0  # For bool slots


class FileReport(BaseModel):
    """Report for a single file."""

    path: str
    total_entries: int
    reviewed_count: int
    slots: dict[str, SlotStats]


class ExportReport(BaseModel):
    """Full export report."""

    total_files: int
    total_entries: int
    total_reviewed: int
    files: list[FileReport]
    global_slot_stats: dict[str, SlotStats]


@router.get("/report")
async def export_report() -> ExportReport:
    """Generate a comprehensive statistics report."""
    file_list = index_directory(settings.data_root)

    file_reports = []
    global_stats: dict[str, dict] = {slot: {"non_null": 0, "true": 0, "false": 0} for slot in ALL_SLOTS}
    total_entries = 0
    total_reviewed = 0

    for file_info in file_list:
        try:
            entries = read_jsonl(file_info.path)
        except Exception:
            continue

        reviewed_count = sum(1 for e in entries if e.get("reviewed", False))
        total_reviewed += reviewed_count
        total_entries += len(entries)

        file_slot_stats: dict[str, SlotStats] = {}

        for slot in ALL_SLOTS:
            non_null = 0
            true_count = 0
            false_count = 0

            for entry in entries:
                value = entry.get("gold", {}).get("slots", {}).get(slot)
                if value is not None:
                    non_null += 1
                    global_stats[slot]["non_null"] += 1
                    if slot in BOOL_SLOTS:
                        if value is True:
                            true_count += 1
                            global_stats[slot]["true"] += 1
                        elif value is False:
                            false_count += 1
                            global_stats[slot]["false"] += 1

            file_slot_stats[slot] = SlotStats(
                total_non_null=non_null,
                true_count=true_count,
                false_count=false_count,
            )

        file_reports.append(
            FileReport(
                path=file_info.relative_path,
                total_entries=len(entries),
                reviewed_count=reviewed_count,
                slots=file_slot_stats,
            )
        )

    return ExportReport(
        total_files=len(file_list),
        total_entries=total_entries,
        total_reviewed=total_reviewed,
        files=file_reports,
        global_slot_stats={
            slot: SlotStats(
                total_non_null=stats["non_null"],
                true_count=stats["true"],
                false_count=stats["false"],
            )
            for slot, stats in global_stats.items()
        },
    )
