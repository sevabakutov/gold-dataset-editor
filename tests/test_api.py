"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestFilesApi:
    """Tests for files API endpoints."""

    def test_list_files(self, test_client):
        """Test listing files."""
        response = test_client.get("/api/files")

        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert data["total_files"] >= 1

    def test_get_file_stats(self, test_client):
        """Test getting file statistics."""
        response = test_client.get("/api/files/test.jsonl/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["entry_count"] == 3
        assert "reviewed_count" in data
        assert "non_null_slots_count" in data

    def test_get_file_stats_not_found(self, test_client):
        """Test getting stats for non-existent file."""
        response = test_client.get("/api/files/nonexistent.jsonl/stats")
        assert response.status_code == 404


class TestEntriesApi:
    """Tests for entries API endpoints."""

    def test_list_entries(self, test_client):
        """Test listing entries."""
        response = test_client.get("/api/files/test.jsonl/entries")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["entries"]) == 3

    def test_list_entries_pagination(self, test_client):
        """Test entry pagination."""
        response = test_client.get("/api/files/test.jsonl/entries?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["entries"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_list_entries_filter_non_null(self, test_client):
        """Test filtering entries with non-null slots."""
        response = test_client.get("/api/files/test.jsonl/entries?filter_non_null=true")

        assert response.status_code == 200
        data = response.json()
        # Entries 1 and 2 have non-null slots
        assert data["total"] == 2

    def test_get_entry(self, test_client):
        """Test getting a single entry."""
        response = test_client.get("/api/files/test.jsonl/entries/0")

        assert response.status_code == 200
        data = response.json()
        assert data["index"] == 0
        assert "entry" in data

    def test_get_entry_not_found(self, test_client):
        """Test getting non-existent entry."""
        response = test_client.get("/api/files/test.jsonl/entries/100")
        assert response.status_code == 404

    def test_patch_entry(self, test_client):
        """Test patching an entry."""
        response = test_client.patch(
            "/api/files/test.jsonl/entries/0",
            json={"slots": {"name": "TestName"}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["entry"]["gold"]["slots"]["name"] == "TestName"
        assert data["has_unsaved"] is True

    def test_patch_entry_evidence(self, test_client):
        """Test patching entry evidence."""
        response = test_client.patch(
            "/api/files/test.jsonl/entries/0",
            json={"evidence": {"name": "Found in message text"}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["entry"]["gold"]["evidence"]["name"] == "Found in message text"

    def test_mark_reviewed(self, test_client):
        """Test marking entry as reviewed."""
        response = test_client.post("/api/files/test.jsonl/entries/0/reviewed")

        assert response.status_code == 200
        data = response.json()
        assert data["entry"]["reviewed"] is True

        # Toggle back
        response = test_client.post("/api/files/test.jsonl/entries/0/reviewed")
        data = response.json()
        assert data["entry"]["reviewed"] is False

    def test_search_entries(self, test_client):
        """Test searching entries."""
        response = test_client.get("/api/files/test.jsonl/search?q=phone")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestExportApi:
    """Tests for export API endpoints."""

    def test_export_report(self, test_client):
        """Test generating export report."""
        response = test_client.get("/api/export/report")

        assert response.status_code == 200
        data = response.json()
        assert "total_files" in data
        assert "total_entries" in data
        assert "global_slot_stats" in data
        assert "files" in data


class TestUIEndpoints:
    """Tests for UI endpoints."""

    def test_index_page(self, test_client):
        """Test the main index page."""
        response = test_client.get("/")

        assert response.status_code == 200
        assert b"Gold" in response.content

    def test_partial_file(self, test_client):
        """Test the partial file content endpoint."""
        response = test_client.get("/partial/file/test.jsonl")

        assert response.status_code == 200
        assert b"entry" in response.content.lower()

    def test_partial_entry(self, test_client):
        """Test the partial entry endpoint."""
        response = test_client.get("/partial/entry/test.jsonl/0")

        assert response.status_code == 200
        assert b"slot" in response.content.lower()
