"""CLIConfig Pydantic model for user's local CLI configuration."""

import os
from pathlib import Path

from pydantic import Field, BaseModel, ConfigDict, field_validator


class CLIConfig(BaseModel):
    """Represents user's local CLI configuration.

    Fields:
        default_repo_url: Default config repository URL
        repo_branch: Default branch to use (default: main)
        user_home: User's home directory path
        config_dir: CLI configuration directory (~/.config/c3cli)
        log_level: Logging level (debug, info, warn, error)

    Validation Rules:
        - Repository URL must be valid Git URL if provided
        - Branch name must be valid Git branch name
        - Paths must be accessible
        - Log level must be valid logging level

    State Transitions:
        - Default config → User customized → Config saved
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

    @field_validator("default_repo_url")
    @classmethod
    def validate_repo_url(cls, v: str | None) -> str | None:
        """Validate repository URL if provided."""
        if v is None:
            return v

        v = v.strip()
        if not v:
            return None

        # Support common Git URL formats
        valid_schemes = ["http://", "https://", "git://", "ssh://", "git@"]
        if not any(v.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(f"Repository URL must start with one of: {', '.join(valid_schemes)}")

        return v

    @field_validator("repo_branch")
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

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        v = v.lower().strip()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v

    @field_validator("default_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate output format."""
        valid_formats = ["text", "json"]
        v = v.lower().strip()
        if v not in valid_formats:
            raise ValueError(f"Output format must be one of: {', '.join(valid_formats)}")
        return v

    @field_validator("user_home", "config_dir", mode="before")
    @classmethod
    def convert_to_path(cls, v) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v).expanduser().resolve()
        return v

    @classmethod
    def get_default_config_dir(cls) -> Path:
        """Get default configuration directory."""
        # Follow XDG Base Directory Specification
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "c3cli"
        return Path.home() / ".config" / "c3cli"

    @classmethod
    def load_from_file(cls, config_path: Path | None = None) -> "CLIConfig":
        """Load configuration from file or create default."""
        if config_path is None:
            config_path = cls.get_default_config_dir() / "config.toml"

        # For now, always create default configuration
        # In tests, they can override the default_repo_url
        config = cls()

        # Ensure config directories exist
        config.ensure_config_dirs()

        return config

    def save_to_file(self, config_path: Path | None = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = self.config_dir / "config.toml"

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # TODO: Implement TOML saving
        # For now, just create an empty file
        config_path.touch()

    def get_repo_cache_dir(self, repo_url: str | None = None) -> Path:
        """Get cache directory for a repository."""
        if repo_url is None:
            repo_url = self.default_repo_url

        if repo_url is None:
            raise ValueError("No repository URL provided")

        # Create a safe directory name from repo URL
        safe_name = repo_url.replace("://", "_").replace("/", "_").replace(".", "_")
        return self.config_dir / "repos" / safe_name

    def ensure_config_dirs(self) -> None:
        """Ensure all configuration directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "repos").mkdir(exist_ok=True)
        (self.config_dir / "state").mkdir(exist_ok=True)

    def get_state_file(self) -> Path:
        """Get path to state file."""
        return self.config_dir / "state" / "application_state.json"

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
