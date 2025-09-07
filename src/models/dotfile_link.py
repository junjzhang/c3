"""DotfileLink Pydantic model for symlinks from user directory to config repository."""

import os
from pathlib import Path
from datetime import datetime

from pydantic import Field, BaseModel, field_validator


class DotfileLink(BaseModel):
    """Represents a symlink from user directory to config repository file.

    Fields:
        source: Path to file in config repository
        target: Path to symlink in user directory
        template_name: Template that created this link
        created_at: When symlink was created

    Validation Rules:
        - Source file must exist in repository
        - Target parent directory must exist or be creatable
        - Target must not conflict with existing file (unless force flag)

    State Transitions:
        - Link planned → Link created → Link verified
    """

    source: Path = Field(..., description="Path to file in config repository")

    target: Path = Field(..., description="Path to symlink in user directory")

    template_name: str = Field(..., min_length=1, description="Template that created this link")

    created_at: datetime = Field(default_factory=datetime.now, description="When symlink was created")

    # Status tracking
    is_valid: bool = Field(default=True, description="Whether the symlink is valid and points to correct source")

    last_verified: datetime | None = Field(None, description="When the link was last verified")

    @field_validator("source", "target", mode="before")
    @classmethod
    def convert_to_path(cls, v) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v).expanduser().resolve()
        return v

    @field_validator("template_name")
    @classmethod
    def validate_template_name(cls, v: str) -> str:
        """Validate template name."""
        v = v.strip()
        if not v:
            raise ValueError("Template name cannot be empty")
        return v

    def exists(self) -> bool:
        """Check if the symlink exists."""
        return self.target.exists() or self.target.is_symlink()

    def is_symlink(self) -> bool:
        """Check if target is a symbolic link."""
        return self.target.is_symlink()

    def is_broken(self) -> bool:
        """Check if symlink exists but points to non-existent file."""
        return self.target.is_symlink() and not self.target.exists()

    def points_to_source(self) -> bool:
        """Check if symlink points to the expected source."""
        if not self.is_symlink():
            return False
        try:
            return self.target.resolve() == self.source.resolve()
        except (OSError, RuntimeError):
            return False

    def verify_link(self) -> bool:
        """Verify that the symlink is valid and points to source."""
        self.last_verified = datetime.now()

        if not self.exists():
            self.is_valid = False
            return False

        if not self.is_symlink():
            self.is_valid = False
            return False

        if self.is_broken():
            self.is_valid = False
            return False

        if not self.points_to_source():
            self.is_valid = False
            return False

        self.is_valid = True
        return True

    def get_status(self) -> str:
        """Get human-readable status of the link."""
        if not self.exists():
            return "missing"

        if not self.is_symlink():
            return "file_exists_not_link"

        if self.is_broken():
            return "broken_link"

        if not self.points_to_source():
            return "wrong_target"

        return "valid"

    def get_relative_source(self) -> Path:
        """Get source path relative to target directory for creating symlink."""
        try:
            return Path(os.path.relpath(self.source, self.target.parent))
        except (ValueError, OSError):
            return self.source

    def can_create_symlink(self) -> tuple[bool, str]:
        """Check if symlink can be created, return (success, reason)."""
        if self.exists() and not self.is_symlink():
            return False, "Target file exists and is not a symlink"

        if not self.source.exists():
            return False, "Source file does not exist"

        # Check if parent directory exists or can be created
        parent = self.target.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                return False, f"Cannot create parent directory: {e}"

        # Check write permissions
        if not os.access(parent, os.W_OK):
            return False, "No write permission to target directory"

        return True, "OK"

    class Config:
        """Pydantic model configuration."""

        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat(),
        }
