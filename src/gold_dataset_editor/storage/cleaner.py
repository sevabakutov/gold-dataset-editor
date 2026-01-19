"""Entry cleaning utilities for reviewed file export."""

from typing import Any


def _remove_nulls(obj: Any) -> Any:
    """Recursively remove null/None values from nested data structures.

    Args:
        obj: The object to clean (dict, list, or scalar)

    Returns:
        The cleaned object with all None values removed
    """
    if isinstance(obj, dict):
        return {k: _remove_nulls(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [_remove_nulls(item) for item in obj if item is not None]
    else:
        return obj


def clean_entry(entry: dict) -> dict:
    """Clean a single entry for reviewed export.

    Removes:
    - gold.evidence section entirely
    - qa_hint field
    - All null/None values recursively

    Args:
        entry: The entry dictionary to clean

    Returns:
        A cleaned copy of the entry
    """
    # Make a deep copy to avoid modifying the original
    import copy
    cleaned = copy.deepcopy(entry)

    # Remove qa_hint field
    cleaned.pop("qa_hint", None)

    # Remove gold.evidence section
    if "gold" in cleaned and isinstance(cleaned["gold"], dict):
        cleaned["gold"].pop("evidence", None)

    # Recursively remove all null values
    cleaned = _remove_nulls(cleaned)

    return cleaned


def clean_entries(entries: list[dict]) -> list[dict]:
    """Clean a batch of entries for reviewed export.

    Args:
        entries: List of entry dictionaries to clean

    Returns:
        List of cleaned entry dictionaries
    """
    return [clean_entry(entry) for entry in entries]
