"""Path resolution logic for CLI configuration."""

import os
from typing import TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from .config_data import ConfigData


class PathResolver:
    """Handles path calculations and directory management for configuration."""

    def __init__(self, config_data: "ConfigData") -> None:
        self.config_data = config_data

    @staticmethod
    def get_default_config_dir() -> Path:
        """Get default configuration directory following XDG Base Directory Specification."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "c3cli"
        return Path.home() / ".config" / "c3cli"

    def get_repo_cache_dir(self, repo_url: str | None = None) -> Path:
        """Get cache directory for a repository."""
        if repo_url is None:
            repo_url = self.config_data.default_repo_url

        if repo_url is None:
            raise ValueError("No repository URL provided")

        # Create a safe directory name from repo URL
        safe_name = repo_url.replace("://", "_").replace("/", "_").replace(".", "_")
        return self.config_data.config_dir / "repos" / safe_name

    def ensure_config_dirs(self) -> None:
        """Ensure all configuration directories exist."""
        self.config_data.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_data.config_dir / "repos").mkdir(exist_ok=True)
        (self.config_data.config_dir / "state").mkdir(exist_ok=True)

    def get_state_file(self) -> Path:
        """Get path to state file."""
        return self.config_data.config_dir / "state" / "application_state.json"
