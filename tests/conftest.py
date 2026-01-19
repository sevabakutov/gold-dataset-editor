"""Test fixtures for gold dataset editor."""

import copy
import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_entry():
    """Return a sample entry dictionary."""
    return {
        "id": "test_message.json:0",
        "source": {
            "drive_path": "test_message.json",
            "thread_dir": "",
            "message_index": 0
        },
        "message": {
            "role": "client",
            "text": "Hello, I want to make an appointment",
            "ts_ms": 1234567890
        },
        "context": [],
        "gold": {
            "slots": {
                "number_phone": None,
                "name": None,
                "location": None,
                "treatment": None,
                "date_time": None,
                "is_first_time": None,
                "has_contraindications": None,
                "is_consultation": None,
                "can_visit_center": None
            },
            "evidence": {
                "number_phone": None,
                "name": None,
                "location": None,
                "treatment": None,
                "date_time": None,
                "is_first_time": None,
                "has_contraindications": None,
                "is_consultation": None,
                "can_visit_center": None
            }
        },
        "qa_hint": None
    }


@pytest.fixture
def sample_jsonl_file(temp_dir, sample_entry):
    """Create a sample JSONL file with test entries."""
    file_path = temp_dir / "test.jsonl"

    # Use deepcopy to ensure independent entries
    entries = [copy.deepcopy(sample_entry) for _ in range(3)]
    entries[0]["id"] = "test_message.json:0"
    entries[1]["id"] = "test_message.json:1"
    entries[1]["message"]["text"] = "My phone number is +380501234567"
    entries[1]["gold"]["slots"]["number_phone"] = "+380501234567"
    entries[2]["id"] = "test_message.json:2"
    entries[2]["message"]["text"] = "I live in Kyiv"
    entries[2]["gold"]["slots"]["location"] = "Kyiv"

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return file_path


@pytest.fixture
def test_client(temp_dir, sample_jsonl_file):
    """Create a test client with configured data root."""
    from gold_dataset_editor.config import settings
    from gold_dataset_editor.app import app, edit_session

    # Update settings
    settings.data_root = temp_dir

    # Clear edit session before each test
    edit_session.clear()

    return TestClient(app)
