"""Configuration file I/O operations."""

from pathlib import Path

import tomli_w
import tomllib

from .config_data import ConfigData
from .config_validator import ConfigValidationMixin


class CLIConfig(ConfigData, ConfigValidationMixin):
    """CLI Configuration with validation and I/O capabilities."""

    @classmethod
    def load_from_file(cls, config_path: Path | None = None) -> "CLIConfig":
        """Load configuration from file or create default."""
        from .config_paths import PathResolver

        if config_path is None:
            config_path = PathResolver.get_default_config_dir() / "config.toml"

        # Try to load existing configuration
        if config_path.exists() and config_path.stat().st_size > 0:
            try:
                with open(config_path, "rb") as f:
                    data = tomllib.load(f)

                # Extract configuration values
                repo_data = data.get("repository", {})
                behavior_data = data.get("behavior", {})
                advanced_data = data.get("advanced", {})

                config = cls(
                    default_repo_url=repo_data.get("url"),
                    repo_branch=repo_data.get("branch", "main"),
                    log_level=behavior_data.get("log_level", "info"),
                    default_format=behavior_data.get("default_format", "text"),
                    auto_sync=behavior_data.get("auto_sync", True),
                    prompt_for_scripts=behavior_data.get("prompt_for_scripts", True),
                    max_parallel_operations=advanced_data.get("max_parallel_operations", 4),
                    sync_timeout=advanced_data.get("sync_timeout", 300),
                )
            except (tomllib.TOMLDecodeError, ValueError, OSError):
                # If config file is corrupted or unreadable, create default
                config = cls()
        else:
            # Create default configuration if file doesn't exist
            config = cls()

        # Ensure config directories exist
        path_resolver = PathResolver(config)
        path_resolver.ensure_config_dirs()

        return config

    def save_to_file(self, config_path: Path | None = None) -> None:
        """Save configuration to file using TOML format."""
        if config_path is None:
            config_path = self.config_dir / "config.toml"

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create configuration data to save
        config_data = {
            "repository": {
                "url": self.default_repo_url,
                "branch": self.repo_branch,
            },
            "behavior": {
                "log_level": self.log_level,
                "default_format": self.default_format,
                "auto_sync": self.auto_sync,
                "prompt_for_scripts": self.prompt_for_scripts,
            },
            "advanced": {
                "max_parallel_operations": self.max_parallel_operations,
                "sync_timeout": self.sync_timeout,
            },
        }

        # Save to TOML file using tomli_w
        with open(config_path, "wb") as f:
            tomli_w.dump(config_data, f)

    def get_repo_cache_dir(self, repo_url: str | None = None) -> Path:
        """Get cache directory for a repository."""
        from .config_paths import PathResolver

        path_resolver = PathResolver(self)
        return path_resolver.get_repo_cache_dir(repo_url)

    def ensure_config_dirs(self) -> None:
        """Ensure all configuration directories exist."""
        from .config_paths import PathResolver

        path_resolver = PathResolver(self)
        path_resolver.ensure_config_dirs()

    def get_state_file(self) -> Path:
        """Get path to state file."""
        from .config_paths import PathResolver

        path_resolver = PathResolver(self)
        return path_resolver.get_state_file()
