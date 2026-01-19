"""Pydantic models for gold dataset entries."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Source(BaseModel):
    """Source information for an entry."""

    drive_path: str
    thread_dir: str = ""
    message_index: int

    model_config = ConfigDict(extra="allow")


class Message(BaseModel):
    """A single message in the conversation."""

    role: str
    text: str
    ts_ms: int

    model_config = ConfigDict(extra="allow")


class Gold(BaseModel):
    """Gold annotation data with slots and evidence."""

    slots: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class Entry(BaseModel):
    """A single entry in the gold dataset."""

    id: str
    source: Source
    message: Message | dict
    context: list[dict] = Field(default_factory=list)
    gold: Gold
    qa_hint: str | None = None
    reviewed: bool = False

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_dict(cls, data: dict) -> "Entry":
        """Create an Entry from a raw dictionary, preserving all fields."""
        return cls.model_validate(data)

    def to_dict(self) -> dict:
        """Convert to dictionary, preserving all fields including extras."""
        return self.model_dump(mode="json")


class SlotUpdate(BaseModel):
    """Update for a single slot value."""

    slot_name: str
    value: Any
    evidence: Any | None = None


class EntryUpdate(BaseModel):
    """Update payload for an entry."""

    slots: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    qa_hint: str | None = None
    reviewed: bool | None = None
    message_role: str | None = None  # Update main message role
    context_updates: list[dict] | None = None  # [{"index": 0, "role": "brand"}]


# Slot type definitions
BOOL_SLOTS = {"is_first_time", "has_contraindications", "is_consultation", "can_visit_center"}
STRING_SLOTS = {
    "number_phone",
    "name",
    "location",
    "treatment",
    "date_time",
    # Treatment-specific slots
    "blood_vessels_area",
    "tattoo_removal_category",
    "tattoo_equipment",
    "hair_removal_type",
    "hair_removal_areas",  # list[str] in data, displayed/edited as comma-separated string
    "hair_type_on_face",
}
ALL_SLOTS = BOOL_SLOTS | STRING_SLOTS
