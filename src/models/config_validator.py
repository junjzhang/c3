"""Configuration validation logic extracted from CLIConfig."""

from pathlib import Path

from pydantic import field_validator


class ConfigValidationMixin:
    """Validation logic for configuration fields."""

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
