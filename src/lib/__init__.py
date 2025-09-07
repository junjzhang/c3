"""Core libraries for Claude Code Configuration Manager CLI."""

from .git_ops import GitOperations
from .dotfiles import DotfilesManager
from .templates import TemplatesManager

__all__ = [
    "DotfilesManager",
    "GitOperations",
    "TemplatesManager",
]
