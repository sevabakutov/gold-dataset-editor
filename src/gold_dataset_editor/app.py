"""FastAPI application for gold dataset editor."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from gold_dataset_editor.api import files, entries, export
from gold_dataset_editor.config import settings
from gold_dataset_editor.models.session import EditSession

# Create FastAPI app
app = FastAPI(
    title="Gold Dataset Editor",
    description="Web-based editor for gold datasets in JSONL format",
    version="0.1.0",
)

# Determine paths relative to this file
_THIS_DIR = Path(__file__).parent
_TEMPLATES_DIR = _THIS_DIR / "templates"
_STATIC_DIR = _THIS_DIR / "static"

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def slot_value_filter(value):
    """Convert slot value to display string (handles lists)."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


templates.env.filters["slot_value"] = slot_value_filter

# Mount static files
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Include API routers
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(entries.router, prefix="/api/files", tags=["entries"])
app.include_router(export.router, prefix="/api/export", tags=["export"])

# Global edit session
edit_session = EditSession()


@app.get("/")
async def index(request: Request):
    """Render the main page."""
    from gold_dataset_editor.storage.indexer import index_directory

    # Get files from output folder (data_root)
    output_files = index_directory(settings.data_root)

    # Get files from reviewed folder
    reviewed_root = settings.reviewed_output_dir or (settings.data_root.parent / "reviewed")
    reviewed_files = []
    if reviewed_root.exists():
        reviewed_files = index_directory(reviewed_root)

    # Get files from skipped folder
    skipped_root = settings.skipped_output_dir or (settings.data_root.parent / "skipped")
    skipped_files = []
    if skipped_root.exists():
        skipped_files = index_directory(skipped_root)

    # Get set of reviewed and skipped file names (relative paths)
    reviewed_names = {f.relative_path for f in reviewed_files}
    skipped_names = {f.relative_path for f in skipped_files}

    # Filter output files - exclude those already in reviewed or skipped
    pending_files = [f for f in output_files if f.relative_path not in reviewed_names and f.relative_path not in skipped_names]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "reviewed_files": reviewed_files,
            "pending_files": pending_files,
            "skipped_files": skipped_files,
            "data_root": str(settings.data_root),
        },
    )


@app.get("/partial/file/{file_id:path}")
async def partial_file(request: Request, file_id: str):
    """Render file content partial (for HTMX)."""
    from gold_dataset_editor.storage.indexer import get_file_by_id
    from gold_dataset_editor.storage.reader import read_jsonl

    # Determine reviewed_root and skipped_root
    reviewed_root = settings.reviewed_output_dir or (settings.data_root.parent / "reviewed")
    skipped_root = settings.skipped_output_dir or (settings.data_root.parent / "skipped")

    file_info = get_file_by_id(settings.data_root, file_id, reviewed_root=reviewed_root, skipped_root=skipped_root)
    if not file_info:
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "error": "File not found"},
            status_code=404,
        )

    entries = read_jsonl(file_info.path)

    return templates.TemplateResponse(
        "partials/file_content.html",
        {
            "request": request,
            "file_info": file_info,
            "file_id": file_id,
            "entries": entries,
            "total_entries": len(entries),
        },
    )


@app.get("/partial/entry/{file_id:path}/{index}")
async def partial_entry(request: Request, file_id: str, index: int):
    """Render single entry partial (for HTMX)."""
    from gold_dataset_editor.storage.indexer import get_file_by_id
    from gold_dataset_editor.storage.reader import read_jsonl
    from gold_dataset_editor.models.entry import BOOL_SLOTS, STRING_SLOTS, INTENTION_TYPES, MULTI_SELECT_SLOTS, SLOT_OPTIONS

    # Determine reviewed_root and skipped_root
    reviewed_root = settings.reviewed_output_dir or (settings.data_root.parent / "reviewed")
    skipped_root = settings.skipped_output_dir or (settings.data_root.parent / "skipped")

    file_info = get_file_by_id(settings.data_root, file_id, reviewed_root=reviewed_root, skipped_root=skipped_root)
    if not file_info:
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "error": "File not found"},
            status_code=404,
        )

    entries = read_jsonl(file_info.path)
    if index < 0 or index >= len(entries):
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "error": "Entry not found"},
            status_code=404,
        )

    entry = entries[index]

    # Check for unsaved version
    unsaved = edit_session.get_unsaved_entry(file_info.path, index)
    if unsaved:
        entry = unsaved

    # Ensure entry has the proper structure for the template
    if "gold" not in entry:
        entry["gold"] = {}
    if "slots" not in entry["gold"]:
        entry["gold"]["slots"] = {}

    return templates.TemplateResponse(
        "partials/entry_card.html",
        {
            "request": request,
            "entry": entry,
            "index": index,
            "file_id": file_id,
            "total_entries": len(entries),
            "bool_slots": BOOL_SLOTS,
            "string_slots": STRING_SLOTS,
            "intention_types": INTENTION_TYPES,
            "multi_select_slots": MULTI_SELECT_SLOTS,
            "slot_options": SLOT_OPTIONS,
            "has_unsaved": unsaved is not None,
        },
    )
