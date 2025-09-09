"""Pure data model for CLI configuration without I/O or validation logic."""

from pathlib import Path

from pydantic import Field, BaseModel, ConfigDict


class ConfigData(BaseModel):
    """Pure data model for CLI configuration.

    Contains only configuration data with basic field definitions.
    All validation, I/O, and path resolution logic is handled by separate classes.
    """

    # Repository settings
    default_repo_url: str | None = Field(None, description="Default config repository URL")
    repo_branch: str = Field(default="main", description="Default branch to use")

    # Path settings
    user_home: Path = Field(default_factory=lambda: Path.home(), description="User's home directory path")
    config_dir: Path = Field(
        default_factory=lambda: Path.home() / ".config" / "c3cli", description="CLI configuration directory"
    )

    # Behavior settings
    log_level: str = Field(default="info", description="Logging level")
    default_format: str = Field(default="text", description="Default output format")
    auto_sync: bool = Field(default=True, description="Automatically sync before operations")
    prompt_for_scripts: bool = Field(default=True, description="Prompt before executing install.sh")

    # Advanced settings
    max_parallel_operations: int = Field(default=4, ge=1, le=16, description="Maximum parallel operations")
    sync_timeout: int = Field(default=300, ge=30, le=3600, description="Git sync timeout in seconds")

    def is_configured(self) -> bool:
        """Check if CLI is configured with a repository."""
        return self.default_repo_url is not None

    def should_auto_sync(self) -> bool:
        """Check if auto-sync is enabled."""
        return self.auto_sync

    def should_prompt_for_scripts(self) -> bool:
        """Check if should prompt before executing scripts."""
        return self.prompt_for_scripts

    model_config = ConfigDict(validate_assignment=True, extra="forbid")
