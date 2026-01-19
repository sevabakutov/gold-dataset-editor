"""Edit session state management."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EntryEdit:
    """Record of a single entry edit."""

    file_path: Path
    entry_index: int
    entry_id: str
    field_path: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EditSession:
    """Track unsaved changes and undo history for a session."""

    # Unsaved changes: {(file_path, entry_index): modified_entry}
    unsaved_changes: dict[tuple[str, int], dict] = field(default_factory=dict)

    # Undo history stack
    undo_stack: list[EntryEdit] = field(default_factory=list)

    # Maximum undo history size
    max_undo_history: int = 100

    def record_change(
        self,
        file_path: Path,
        entry_index: int,
        entry_id: str,
        field_path: str,
        old_value: Any,
        new_value: Any,
        modified_entry: dict,
    ) -> None:
        """Record a change for potential undo and track unsaved state."""
        edit = EntryEdit(
            file_path=file_path,
            entry_index=entry_index,
            entry_id=entry_id,
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
        )

        self.undo_stack.append(edit)
        if len(self.undo_stack) > self.max_undo_history:
            self.undo_stack.pop(0)

        key = (str(file_path), entry_index)
        self.unsaved_changes[key] = modified_entry

    def mark_saved(self, file_path: Path) -> None:
        """Mark all changes for a file as saved."""
        file_str = str(file_path)
        keys_to_remove = [k for k in self.unsaved_changes if k[0] == file_str]
        for key in keys_to_remove:
            del self.unsaved_changes[key]

    def has_unsaved_changes(self, file_path: Path | None = None) -> bool:
        """Check if there are unsaved changes."""
        if file_path is None:
            return bool(self.unsaved_changes)
        file_str = str(file_path)
        return any(k[0] == file_str for k in self.unsaved_changes)

    def get_unsaved_entry(self, file_path: Path, entry_index: int) -> dict | None:
        """Get the unsaved version of an entry if it exists."""
        key = (str(file_path), entry_index)
        return self.unsaved_changes.get(key)

    def clear(self) -> None:
        """Clear all session state."""
        self.unsaved_changes.clear()
        self.undo_stack.clear()
