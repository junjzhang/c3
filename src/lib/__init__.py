"""Core libraries for Claude Code Configuration Manager CLI."""

from .git_ops import GitOperations
from .dotfiles import DotfilesManager
from .templates import TemplatesManager
from .command_base import (
    CommandError,
    ConflictError,
    CommandContext,
    RepositoryError,
    ConfigurationError,
    get_command_context,
    handle_command_error,
    create_command_context,
    ensure_repository_configured,
)

__all__ = [
    "DotfilesManager",
    "GitOperations",
    "TemplatesManager",
    "CommandContext",
    "CommandError",
    "RepositoryError",
    "ConfigurationError",
    "ConflictError",
    "create_command_context",
    "ensure_repository_configured",
    "handle_command_error",
    "get_command_context",
]
