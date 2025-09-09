"""Command base infrastructure for CLI commands.

This module provides unified command infrastructure to eliminate code duplication
across CLI commands. Every command should use these utilities instead of
manually parsing context and handling errors.
"""

import logging
from dataclasses import dataclass

import click
import typer
from rich.console import Console

from ..models.config_loader import CLIConfig

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class CommandContext:
    """Unified command context with all necessary configuration.

    This eliminates the need for each command to parse ctx.obj manually.
    All configuration loading and validation happens once in main.py.
    """

    config: CLIConfig
    verbose: bool = False
    output_format: str = "text"

    @property
    def is_json_output(self) -> bool:
        """Check if output format is JSON."""
        return self.output_format == "json"

    @classmethod
    def from_cli_args(
        cls,
        config_path: str | None,
        repo_override: str | None,
        verbose: bool,
        quiet: bool,  # noqa
        format_type: str | None,
    ) -> "CommandContext":
        """Create CommandContext directly from CLI arguments.

        This eliminates the need for intermediate dict conversion and
        centralizes all configuration loading logic.

        Args:
            config_path: Path to config file or None
            repo_override: Repository URL override or None
            verbose: Verbose logging flag
            quiet: Quiet logging flag (unused in context but available)
            format_type: Output format string

        Returns:
            CommandContext with loaded configuration

        Raises:
            ConfigurationError: If configuration is invalid
            RepositoryError: If repository URL is invalid
        """
        from pathlib import Path

        try:
            # Load configuration
            config = CLIConfig.load_from_file(Path(config_path) if config_path else None)

            # Apply repository override if provided
            if repo_override:
                try:
                    config.default_repo_url = repo_override
                except Exception as e:
                    raise RepositoryError(f"Invalid repository URL: {e}")

            # Resolve output format: CLI option overrides config
            resolved_format = format_type or config.default_format

            return cls(config=config, verbose=verbose, output_format=resolved_format)

        except Exception as e:
            logger.error(f"Failed to create command context: {e}")
            raise CommandError.from_exception(e)


class CommandError(Exception):
    """Base exception for command errors with specific exit codes."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)

    @classmethod
    def from_exception(cls, error: Exception) -> "CommandError":
        """Create appropriate CommandError from any exception."""
        if isinstance(error, CommandError):
            return error

        # Categorize common error types
        error_str = str(error).lower()
        if any(keyword in error_str for keyword in ["repository", "git", "clone", "fetch", "remote"]):
            return RepositoryError(str(error))
        elif any(keyword in error_str for keyword in ["config", "toml", "validation", "invalid"]):
            return ConfigurationError(str(error))
        elif any(keyword in error_str for keyword in ["conflict", "exists", "permission"]):
            return ConflictError(str(error))
        else:
            return cls(str(error))


class RepositoryError(CommandError):
    """Repository-related errors (exit code 4)."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=4)


class ConfigurationError(CommandError):
    """Configuration-related errors (exit code 1)."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=1)


class ConflictError(CommandError):
    """File conflict errors (exit code 2)."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=2)


def create_command_context(ctx_obj: CommandContext) -> CommandContext:
    """Return the already-initialized unified command context.

    All commands expect `ctx.obj` to be a CommandContext populated in main callback.
    The legacy dict-based context has been removed to simplify behavior.

    Raises:
        ConfigurationError: If context object is not initialized properly
    """
    if isinstance(ctx_obj, CommandContext):
        return ctx_obj
    raise ConfigurationError("Internal error: command context not initialized")


def ensure_repository_configured(context: CommandContext) -> None:
    """Ensure repository is configured, raise error if not.

    Args:
        context: Command context to check

    Raises:
        ConfigurationError: If no repository is configured
    """
    if not context.config.is_configured():
        raise ConfigurationError("No repository configured. Use 'c3cli config set repository.url <url>'")


def handle_command_error(error: Exception) -> None:
    """Handle command errors with consistent formatting and exit codes."""
    if isinstance(error, typer.Exit):
        raise

    # Convert to CommandError if needed
    cmd_error = CommandError.from_exception(error)
    console.print(f"[red]Error: {cmd_error.message}[/red]")
    raise typer.Exit(cmd_error.exit_code)


def get_command_context() -> CommandContext:
    """Get command context from current click context.

    This is a convenience function for commands that need to access
    the unified command context.

    Returns:
        CommandContext for current command

    Raises:
        ConfigurationError: If context cannot be created
    """
    ctx = click.get_current_context()
    return create_command_context(ctx.obj)


def sync_repo_if_needed(
    context: CommandContext,
    git_ops,
    *,
    branch: str | None = None,
    force: bool = False,
) -> None:
    """Ensure repository cache is present and up to date when needed.

    Centralizes the common "clone or sync" logic used by multiple commands.

    Args:
        context: Unified command context
        git_ops: GitOperations instance
        branch: Optional branch override (defaults to config branch)
        force: Force sync (discard local changes)

    Raises:
        RepositoryError: When clone/sync fails
    """
    repo_cache_dir = context.config.get_repo_cache_dir()
    sync_branch = branch if branch is not None else context.config.repo_branch

    need_sync = (not repo_cache_dir.exists()) or context.config.should_auto_sync()
    if not need_sync:
        return

    if context.output_format == "text" and context.verbose:
        console.print(f"Syncing repository from {context.config.default_repo_url}")

    try:
        git_ops.ensure_repo(context.config.default_repo_url, sync_branch, repo_cache_dir, force=force)
    except Exception as e:
        if isinstance(e, RepositoryError):
            raise
        logger.error(f"Repository sync failed: {e}")
        raise RepositoryError("Failed to prepare repository cache")
