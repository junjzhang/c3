"""Enumeration types for CLI operations."""

from enum import Enum


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


class TemplateKind(str, Enum):
    ALL = "all"
    DOTFILES = "dotfiles"
    PROJECTS = "projects"
