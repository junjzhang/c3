"""ConfigRepository Pydantic model for Git repository containing templates."""

from pathlib import Path
from datetime import datetime

from pydantic import Field, BaseModel, ConfigDict, field_validator

from .template import Template


class ConfigRepository(BaseModel):
    """Represents the Git repository containing templates and dotfiles.

    Fields:
        url: Git repository URL
        local_path: Local filesystem path where repo is cloned
        branch: Git branch to use (default: main)
        templates: Available templates indexed by name
        last_sync: Timestamp of last successful sync

    Validation Rules:
        - URL must be valid Git repository URL
        - Local path must be writable directory
        - Branch must exist in remote repository

    State Transitions:
        - Repository configured → Repository cloned → Repository synced
    """

    url: str = Field(..., description="Git repository URL")

    local_path: Path = Field(..., description="Local filesystem path where repo is cloned")

    branch: str = Field(default="main", description="Git branch to use")

    templates: dict[str, Template] = Field(default_factory=dict, description="Available templates indexed by name")

    last_sync: datetime | None = Field(None, description="Timestamp of last successful sync")

    # Internal tracking fields
    clone_status: str = Field(default="not_cloned", description="Repository clone status")

    sync_in_progress: bool = Field(default=False, description="Whether sync operation is currently running")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL is a valid Git repository URL."""
        v = v.strip()
        if not v:
            raise ValueError("Repository URL cannot be empty")

        # Support common Git URL formats
        valid_schemes = ["http://", "https://", "git://", "ssh://", "git@"]
        if not any(v.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(f"Repository URL must start with one of: {', '.join(valid_schemes)}")

        return v

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: str) -> str:
        """Validate branch name."""
        v = v.strip()
        if not v:
            raise ValueError("Branch name cannot be empty")

        # Basic Git branch name validation
        invalid_chars = [" ", "..", "~", "^", ":", "?", "*", "[", "\\"]
        for char in invalid_chars:
            if char in v:
                raise ValueError(f"Branch name cannot contain: {char}")

        if v.startswith("/") or v.endswith("/") or v.endswith("."):
            raise ValueError("Invalid branch name format")

        return v

    @field_validator("local_path", mode="before")
    @classmethod
    def validate_local_path(cls, v) -> Path:
        """Validate and convert local path."""
        if isinstance(v, str):
            v = Path(v).expanduser().resolve()
        elif isinstance(v, Path):
            v = v.expanduser().resolve()
        else:
            raise ValueError("Local path must be a string or Path object")

        return v

    def is_cloned(self) -> bool:
        """Check if repository is cloned locally."""
        return self.clone_status == "cloned" and self.local_path.exists() and (self.local_path / ".git").exists()

    def needs_sync(self) -> bool:
        """Check if repository needs syncing."""
        if not self.is_cloned():
            return True
        if self.last_sync is None:
            return True
        # Consider repository stale if not synced in last hour
        return (datetime.now() - self.last_sync).total_seconds() > 3600

    def get_template_path(self, template_name: str, template_type: str) -> Path:
        """Get path to a specific template directory."""
        type_dir = "dotfiles" if template_type == "dotfiles" else "projects"
        return self.local_path / type_dir / template_name

    def add_template(self, template: Template) -> None:
        """Add a template to the repository."""
        self.templates[template.name] = template

    def remove_template(self, template_name: str) -> bool:
        """Remove a template from the repository."""
        if template_name in self.templates:
            del self.templates[template_name]
            return True
        return False

    def get_template(self, template_name: str) -> Template | None:
        """Get a template by name."""
        return self.templates.get(template_name)

    def list_templates(self, template_type: str | None = None) -> list[Template]:
        """List all templates, optionally filtered by type."""
        templates = list(self.templates.values())
        if template_type:
            templates = [t for t in templates if t.type == template_type]
        return sorted(templates, key=lambda t: t.name)

    def get_dotfiles_path(self) -> Path:
        """Get path to dotfiles directory."""
        return self.local_path / "dotfiles"

    def get_projects_path(self) -> Path:
        """Get path to projects directory."""
        return self.local_path / "projects"

    def mark_synced(self) -> None:
        """Mark repository as recently synced."""
        self.last_sync = datetime.now()
        self.clone_status = "cloned"
        self.sync_in_progress = False

    def mark_sync_started(self) -> None:
        """Mark sync operation as started."""
        self.sync_in_progress = True

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_encoders={
            Path: str,
            datetime: lambda v: v.isoformat(),
        },
    )
