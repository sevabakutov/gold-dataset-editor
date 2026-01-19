# Gold Dataset Editor

A web-based editor for viewing and editing gold datasets in JSONL format, designed for the gold_annotator pipeline.

## Features

- Browse and edit JSONL gold dataset files
- View message context and conversation history
- Edit slot values (string and boolean types)
- Tri-state toggle for boolean slots (True/False/Null)
- Evidence annotation per slot
- QA hints for quality assurance
- Keyboard shortcuts for efficient editing
- Atomic file writes with backup support
- Audit logging for all edits
- Field validation warnings (phone numbers, dates)

## Installation

### Using pip

```bash
cd gold_dataset_editor
pip install -e .
```

### Using pip with dev dependencies (for testing)

```bash
pip install -e ".[dev]"
```

## Usage

### Start the editor

```bash
python -m gold_dataset_editor --data-root /path/to/jsonl/files
```

Or using the installed command:

```bash
gold-dataset-editor --data-root /path/to/jsonl/files
```

### Options

- `--data-root` (required): Root directory containing JSONL files
- `--host`: Host to bind to (default: 127.0.0.1)
- `--port`: Port to bind to (default: 8000)
- `--reload`: Enable auto-reload for development

### Example

```bash
python -m gold_dataset_editor --data-root ./gold_annotator/output --port 8080
```

Then open http://127.0.0.1:8080 in your browser.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `j` / `↓` | Next entry |
| `k` / `↑` | Previous entry |
| `g` | Jump to entry |
| `Ctrl+S` | Save changes |
| `r` | Toggle reviewed |
| `1` | Set boolean slot to True |
| `2` | Set boolean slot to False |
| `3` | Set boolean slot to Null |
| `/` | Focus search |
| `Esc` | Clear focus |

## Slot Types

### String Slots
- `number_phone` - Phone number (E.164 format validation)
- `name` - Client name
- `location` - Location/city
- `treatment` - Treatment type
- `date_time` - Date/time (ISO 8601 format validation)

### Boolean Slots (Tri-state: True/False/Null)
- `is_first_time` - First visit?
- `has_contraindications` - Has contraindications?
- `is_consultation` - Consultation request?
- `can_visit_center` - Can visit center?

## Data Format

The editor works with JSONL files containing entries in this format:

```json
{
  "id": "message_1.json:0",
  "source": {
    "drive_path": "message_1.json",
    "thread_dir": "",
    "message_index": 0
  },
  "message": {
    "role": "client",
    "text": "Hello",
    "ts_ms": 1234567890
  },
  "context": [],
  "gold": {
    "slots": {
      "number_phone": null,
      "name": null,
      "location": null,
      "treatment": null,
      "date_time": null,
      "is_first_time": null,
      "has_contraindications": null,
      "is_consultation": null,
      "can_visit_center": null
    },
    "evidence": {}
  },
  "qa_hint": null
}
```

## Docker

### Build

```bash
docker build -t gold-dataset-editor .
```

### Run

```bash
docker run -p 8000:8000 -v /path/to/data:/data gold-dataset-editor
```

## Development

### Run tests

```bash
pytest tests/
```

### Run with auto-reload

```bash
python -m gold_dataset_editor --data-root ./data --reload
```

## API Endpoints

### Files
- `GET /api/files` - List all JSONL files
- `GET /api/files/{file_id}/stats` - Get file statistics

### Entries
- `GET /api/files/{file_id}/entries` - List entries (paginated)
- `GET /api/files/{file_id}/entries/{index}` - Get single entry
- `PATCH /api/files/{file_id}/entries/{index}` - Update entry
- `POST /api/files/{file_id}/entries/{index}/reviewed` - Toggle reviewed
- `POST /api/files/{file_id}/save` - Save file
- `GET /api/files/{file_id}/search?q=...` - Search entries

### Export
- `GET /api/export/report` - Generate statistics report

## Configuration

Environment variables (prefix: `GOLD_EDITOR_`):

- `GOLD_EDITOR_DATA_ROOT` - Root directory for JSONL files
- `GOLD_EDITOR_HOST` - Host to bind to
- `GOLD_EDITOR_PORT` - Port to bind to
- `GOLD_EDITOR_BACKUP_ON_SAVE` - Create backup before saving (true/false)
