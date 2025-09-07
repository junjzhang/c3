"""Claude Code Configuration Manager CLI.

A CLI tool for managing dotfiles and project templates from Git repositories.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("c3cli")
except PackageNotFoundError:
    # Development mode fallback
    __version__ = "dev"

__author__ = "junjzhang"
