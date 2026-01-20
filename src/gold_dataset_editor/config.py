"""Configuration settings for gold dataset editor."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    data_root: Path = Field(default=Path("."), description="Root directory for JSONL files")
    host: str = Field(default="127.0.0.1", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    backup_on_save: bool = Field(default=True, description="Create backup before saving")
    autosave_interval: int = Field(default=0, description="Autosave interval in seconds (0 = disabled)")
    save_mode: Literal["inplace", "separate"] = Field(default="inplace", description="Save mode")
    slots_schema: Path = Field(default=Path("slots_schema.yaml"), description="Path to slots schema")
    edits_log: Path = Field(default=Path("edits.log"), description="Path to audit log")
    reviewed_output_dir: Path | None = Field(default=None, description="Output directory for reviewed files")
    skipped_output_dir: Path | None = Field(default=None, description="Output directory for skipped files")

    model_config = {"env_prefix": "GOLD_EDITOR_"}


# Global settings instance
settings = Settings()
