"""ProjectFile Pydantic model for files copied from template to project."""

import os
import hashlib
from pathlib import Path
from datetime import datetime

from pydantic import Field, BaseModel, field_validator


class ProjectFile(BaseModel):
    """Represents a file copied from template to project directory.

    Fields:
        source: Path to file in template
        target: Path to copied file in project
        template_name: Template that created this file
        copied_at: When file was copied
        checksum: SHA256 hash of copied content

    Validation Rules:
        - Source file must exist in template
        - Target directory must be writable
        - Checksum must match source file at copy time

    State Transitions:
        - Copy planned → Copy executed → Copy verified
    """

    source: Path = Field(..., description="Path to file in template")

    target: Path = Field(..., description="Path to copied file in project")

    template_name: str = Field(..., min_length=1, description="Template that created this file")

    copied_at: datetime = Field(default_factory=datetime.now, description="When file was copied")

    checksum: str = Field(..., description="SHA256 hash of copied content")

    # File metadata
    file_size: int | None = Field(None, description="Size of the file in bytes")

    file_mode: int | None = Field(None, description="File permissions mode")

    @field_validator("source", "target", mode="before")
    @classmethod
    def convert_to_path(cls, v) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v).expanduser().resolve()
        return v

    @field_validator("checksum")
    @classmethod
    def validate_checksum(cls, v: str) -> str:
        """Validate SHA256 checksum format."""
        v = v.strip().lower()
        if len(v) != 64:
            raise ValueError("Checksum must be 64 characters long")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("Checksum must be valid hexadecimal")
        return v

    @classmethod
    def create_from_copy(cls, source: Path, target: Path, template_name: str) -> "ProjectFile":
        """Create ProjectFile instance after copying file."""
        if not source.exists():
            raise FileNotFoundError(f"Source file does not exist: {source}")

        # Calculate checksum of source file
        checksum = cls.calculate_checksum(source)
        file_size = source.stat().st_size
        file_mode = source.stat().st_mode

        return cls(
            source=source,
            target=target,
            template_name=template_name,
            checksum=checksum,
            file_size=file_size,
            file_mode=file_mode,
        )

    @staticmethod
    def calculate_checksum(file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError as e:
            raise RuntimeError(f"Failed to calculate checksum for {file_path}: {e}")

    def exists(self) -> bool:
        """Check if the copied file exists."""
        return self.target.exists()

    def verify_integrity(self) -> bool:
        """Verify that copied file matches source checksum."""
        if not self.exists():
            return False

        try:
            current_checksum = self.calculate_checksum(self.target)
            return current_checksum == self.checksum
        except RuntimeError:
            return False

    def verify_source_match(self) -> bool:
        """Verify that target file still matches source file."""
        if not self.exists() or not self.source.exists():
            return False

        try:
            source_checksum = self.calculate_checksum(self.source)
            target_checksum = self.calculate_checksum(self.target)
            return source_checksum == target_checksum
        except RuntimeError:
            return False

    def is_modified(self) -> bool:
        """Check if the target file has been modified since copying."""
        return not self.verify_integrity()

    def get_status(self) -> str:
        """Get human-readable status of the copied file."""
        if not self.exists():
            return "missing"

        if not self.verify_integrity():
            return "modified"

        if self.source.exists() and not self.verify_source_match():
            return "source_changed"

        return "valid"

    def can_overwrite(self) -> tuple[bool, str]:
        """Check if file can be overwritten, return (success, reason)."""
        if not self.target.exists():
            return True, "Target does not exist"

        # Check write permissions
        if not os.access(self.target, os.W_OK):
            return False, "No write permission to target file"

        # Check if parent directory is writable
        if not os.access(self.target.parent, os.W_OK):
            return False, "No write permission to target directory"

        return True, "OK"

    def update_checksum(self) -> bool:
        """Update checksum to match current target file."""
        if not self.exists():
            return False

        try:
            self.checksum = self.calculate_checksum(self.target)
            self.copied_at = datetime.now()

            # Update file metadata
            stat = self.target.stat()
            self.file_size = stat.st_size
            self.file_mode = stat.st_mode

            return True
        except RuntimeError:
            return False

    class Config:
        """Pydantic model configuration."""

        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat(),
        }
