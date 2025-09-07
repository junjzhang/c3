# c3 Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-07

## Active Technologies
- Python 3.11+ with Pydantic + Typer + GitPython + Pixi (001-cli-claude-code)

## Project Structure
```
src/
├── dotfiles/           # Symlink management library
├── templates/          # File copying library  
├── git_ops/           # Repository operations library
└── cli/               # Typer CLI facade

tests/
├── contract/          # Contract tests for CLI commands
├── integration/       # Git + filesystem integration tests
└── unit/             # Unit tests for data models
```

## Commands
# CLI tool with subcommands:
- c3cli install <template>  # Apply dotfiles (symlinks)
- c3cli apply <template>    # Apply project templates (copies)
- c3cli list [pattern]      # Show available templates
- c3cli sync               # Update from Git repository
- c3cli status             # Show installation status
- c3cli config             # Manage configuration

## Code Style
Python: Follow standard conventions with Pydantic models, Typer CLI framework, structured logging
Use PEP585 type hint, for example, use list directly instead of List from typing.

## Testing Strategy
- TDD mandatory: Tests written → User approved → Tests fail → Then implement
- Real dependencies (actual Git repos, filesystem operations)
- Order: Contract → Integration → Unit tests

## Recent Changes
- 001-cli-claude-code: Added Python CLI tool for dotfiles/templates management with Pydantic + Typer + GitPython