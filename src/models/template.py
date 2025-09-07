"""Template Pydantic model for configuration templates."""

from enum import Enum
from typing import Any
from pathlib import Path
from datetime import datetime

from pydantic import Field, BaseModel, field_validator


class TemplateType(str, Enum):
    """Template application scope types."""

    DOTFILES = "dotfiles"  # User scope - creates symlinks
    PROJECT = "project"  # Repo scope - copies files


class Template(BaseModel):
    """Represents a configuration template that can be applied to user or project scope.

    Fields:
        name: Unique template identifier
        description: Human-readable description of template purpose
        type: Either "dotfiles" (user scope) or "project" (repo scope)
        files: List of file paths within template directory
        install_script: Path to install.sh if present
        metadata: Additional metadata from metadata.toml

    Validation Rules:
        - Name must be valid directory name (no special chars)
        - Description required and non-empty
        - Files list must contain at least one file
        - Install script path must exist if specified

    State Transitions:
        - Template discovered → Template validated → Template applied
    """

    name: str = Field(..., min_length=1, description="Unique template identifier")

    description: str = Field(..., min_length=1, description="Human-readable description of template purpose")

    type: TemplateType = Field(..., description="Template application scope (dotfiles or project)")

    files: list[str] = Field(..., min_length=1, description="List of file paths within template directory")

    install_script: str | None = Field(None, description="Path to install.sh if present")

    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata from metadata.toml")

    # Internal fields for tracking
    discovered_at: datetime | None = Field(None, description="When template was discovered in repository")

    template_path: Path | None = Field(None, description="Full path to template directory")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is a valid directory name."""
        if not v.replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise ValueError(
                "Template name must be a valid directory name (alphanumeric, hyphens, underscores, dots only)"
            )
        if v.startswith(".") or v.endswith("."):
            raise ValueError("Template name cannot start or end with a dot")
        return v

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: list[str]) -> list[str]:
        """Validate that all file paths are relative and non-empty."""
        if not v:
            raise ValueError("Template must contain at least one file")

        for file_path in v:
            if not file_path.strip():
                raise ValueError("File paths cannot be empty")
            if Path(file_path).is_absolute():
                raise ValueError(f"File path must be relative, got: {file_path}")

        return v

    @field_validator("install_script", mode="before")
    @classmethod
    def validate_install_script(cls, v: str | None) -> str | None:
        """Validate install script path if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if Path(v).is_absolute():
                raise ValueError(f"Install script path must be relative, got: {v}")
        return v

    def has_install_script(self) -> bool:
        """Check if template has an install script."""
        return self.install_script is not None and bool(self.install_script.strip())

    def get_install_script_path(self) -> Path | None:
        """Get full path to install script if it exists."""
        if not self.has_install_script() or self.template_path is None:
            return None
        return self.template_path / self.install_script

    def get_file_paths(self) -> list[Path]:
        """Get full paths to all template files."""
        if self.template_path is None:
            return [Path(f) for f in self.files]
        return [self.template_path / f for f in self.files]

    def is_dotfiles_template(self) -> bool:
        """Check if this is a dotfiles template."""
        return self.type == TemplateType.DOTFILES

    def is_project_template(self) -> bool:
        """Check if this is a project template."""
        return self.type == TemplateType.PROJECT

    model_config = {"use_enum_values": True, "validate_assignment": True, "extra": "forbid"}
