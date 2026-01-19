# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Gold Dataset Editor is a web-based JSONL editor for annotating gold datasets used in the gold_annotator pipeline. It's a FastAPI application with Jinja2 templates and vanilla JavaScript frontend.

## Commands

```bash
# Install (editable mode)
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run the editor
python -m gold_dataset_editor --data-root /path/to/jsonl/files

# Run with auto-reload for development
python -m gold_dataset_editor --data-root ./data --reload

# Run tests
pytest tests/

# Run single test file
pytest tests/test_reader.py

# Run single test
pytest tests/test_reader.py::test_function_name
```

## Architecture

### Data Flow
1. **CLI** (`cli.py`) parses args and starts uvicorn server
2. **FastAPI app** (`app.py`) serves HTML pages and API endpoints
3. **EditSession** (`models/session.py`) holds unsaved changes in memory
4. **Storage layer** reads/writes JSONL files atomically with backup support

### Key Components

- **EditSession** (`models/session.py`): In-memory store for unsaved edits. Changes are stored per `(file_path, entry_index)` key until explicitly saved. Tracks undo history.

- **Storage layer** (`storage/`):
  - `reader.py`: JSONL parsing with lazy loading option
  - `writer.py`: Atomic writes using temp file + rename pattern, backup creation, audit logging
  - `indexer.py`: File discovery, file IDs use `__` as path separator for URL safety

- **Entry model** (`models/entry.py`): Pydantic models use `extra="allow"` to preserve unknown fields. Defines slot types (`STRING_SLOTS`, `BOOL_SLOTS`), multi-select slots with predefined options (`SLOT_OPTIONS`).

### API Structure
- `/api/files/` - File listing and stats
- `/api/files/{file_id}/entries` - Entry CRUD with pagination and filters
- `/api/files/{file_id}/save` - Persist unsaved changes to disk
- `/api/export/` - Statistics export

### Frontend
- HTMX-driven partials in `templates/partials/`
- Entry editing happens in-browser, changes sent via PATCH to session
- Save (Ctrl+S) commits all session changes to disk

### Role Synchronization
When a message role is changed, the system propagates the change to all entries containing messages with the same `ts_ms` timestamp (see `_propagate_role_change` in `api/entries.py`).

## Configuration

Environment variables (prefix `GOLD_EDITOR_`):
- `GOLD_EDITOR_DATA_ROOT` - Root directory for JSONL files
- `GOLD_EDITOR_BACKUP_ON_SAVE` - Create backup before saving (default: true)

## Testing

Tests use `pytest-asyncio` with `asyncio_mode = "auto"`. The `test_client` fixture creates a FastAPI TestClient with a temp directory as data root.
