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

    file_list = index_directory(settings.data_root)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "files": file_list,
            "data_root": str(settings.data_root),
        },
    )


@app.get("/partial/file/{file_id:path}")
async def partial_file(request: Request, file_id: str):
    """Render file content partial (for HTMX)."""
    from gold_dataset_editor.storage.indexer import get_file_by_id
    from gold_dataset_editor.storage.reader import read_jsonl

    file_info = get_file_by_id(settings.data_root, file_id)
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

    file_info = get_file_by_id(settings.data_root, file_id)
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
