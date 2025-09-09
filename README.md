# c3cli

**Claude Code Configuration Manager CLI**

A simple CLI tool for managing dotfiles (symlinks) and project templates (file copying) from Git repositories. Supports modular configuration management with automatic repository synchronization.

## Features

- **Dotfiles Management**: Create symbolic links to configuration files in your home directory
- **Project Templates**: Copy template files to initialize new projects  
- **Git Integration**: Sync templates from remote Git repositories with automatic caching
- **Flexible Configuration**: Multiple output formats (text/JSON) with comprehensive settings
- **Install Scripts**: Optional post-installation script execution

## Installation

Install using pixi (recommended):

```bash
pixi global install c3cli
```

Or install from source:

```bash
git clone https://github.com/your-org/c3cli
cd c3cli
pixi install -e .
```

## Quick Start

### 1. Configure Repository

```bash
# Set your dotfiles repository
c3cli config set repository.url https://github.com/your/dotfiles-repo

# Verify configuration
c3cli config show
```

### 2. List Available Templates

```bash
# List all templates
c3cli list

# Filter by type
c3cli list --type dotfiles
c3cli list --type projects
```

### 3. Use Templates

```bash
# Install dotfiles (creates symlinks to home directory)
c3cli install vim

# Apply project template (copies files to current directory)  
c3cli apply python-project

# Check status
c3cli status
```

## Commands

| Command | Description |
|---------|-------------|
| `c3cli install <template>` | Apply dotfiles template using symbolic links |
| `c3cli apply <template>` | Apply project template by copying files |
| `c3cli list [pattern]` | List available templates with optional filtering |
| `c3cli sync` | Synchronize with remote configuration repository |
| `c3cli status` | Show status of installed templates and symlinks |
| `c3cli config` | Manage CLI configuration (list/get/set/unset/reset) |

### Command Options

```bash
# Global options
--repo URL          # Override configured repository URL  
--format text|json  # Output format
--verbose           # Enable detailed logging
--quiet             # Suppress non-error output

# List command
c3cli list [pattern] --type all|dotfiles|projects --detailed

# Install/Apply commands  
c3cli install <template> --dry-run --force
c3cli apply <template> --target DIR --dry-run --force --no-script
```

## Configuration

Configuration is stored in `~/.config/c3cli/config.toml`. All settings can be managed via `c3cli config` commands.

### Available Settings

| Key | Description | Default |
|-----|-------------|---------|
| `repository.url` | Git repository URL containing templates | *None* (required) |
| `repository.branch` | Git branch to use | `main` |
| `behavior.log_level` | Logging level (debug/info/warning/error/critical) | `info` |
| `behavior.default_format` | Default output format (text/json) | `text` |
| `behavior.auto_sync` | Automatically sync before operations | `true` |
| `behavior.prompt_for_scripts` | Prompt before executing install.sh | `true` |
| `advanced.max_parallel_operations` | Maximum parallel operations (1-16) | `4` |
| `advanced.sync_timeout` | Git sync timeout in seconds (30-3600) | `300` |

### Configuration Examples

```bash
# Repository settings
c3cli config set repository.url git@github.com:user/dotfiles.git
c3cli config set repository.branch develop

# Behavior settings
c3cli config set behavior.default_format json
c3cli config set behavior.auto_sync false

# Advanced settings
c3cli config set advanced.sync_timeout 600

# View all settings
c3cli config list --format json
```

## Repository Structure

Your Git repository should follow this structure:

```
your-dotfiles-repo/
├── dotfiles/              # Symlink templates (user scope)
│   ├── vim/
│   │   ├── .vimrc         # → symlinked to ~/.vimrc
│   │   └── .vim/plugins/  # → individual files symlinked
│   ├── zsh/
│   │   ├── .zshrc         # → symlinked to ~/.zshrc
│   │   └── .zsh/          # → individual files symlinked  
│   └── nvim/
│       └── .config/nvim/  # → files symlinked to ~/.config/nvim/
│           ├── init.lua
│           └── lua/plugins.lua
└── projects/              # Copy templates (project scope)
    ├── python-project/
    │   ├── pyproject.toml # → copied to ./pyproject.toml
    │   ├── src/           # → copied to ./src/
    │   ├── tests/         # → copied to ./tests/
    │   └── install.sh     # Optional setup script
    └── react-app/
        ├── package.json   # → copied to ./package.json
        ├── src/           # → copied to ./src/
        └── metadata.toml  # Optional template metadata
```

### Special Files

- `metadata.toml` - Template metadata (not copied/linked)
- `install.sh` - Optional post-installation script (not copied/linked)

## Examples

### Basic Workflow

```bash
# Configure
c3cli config set repository.url https://github.com/user/dotfiles

# Install specific dotfiles
c3cli install vim zsh nvim

# Create new project  
mkdir my-project && cd my-project
c3cli apply python-project

# Check what's installed
c3cli status --format json
```

### Selective Configuration Management

```bash
# Install only specific .config subdirectories
c3cli install nvim      # Only ~/.config/nvim/
c3cli install alacritty # Only ~/.config/alacritty/

# List by type with filtering
c3cli list "py*" --type projects --detailed
c3cli list "*vim*" --type dotfiles
```

## Shell Completion

Enable shell completion for enhanced CLI experience:

```bash
# Install completion for current shell
c3cli --install-completion

# Manual setup (if needed)
c3cli --show-completion bash >> ~/.bashrc
c3cli --show-completion zsh >> ~/.zshrc
```

## Troubleshooting

**No repository configured**: `c3cli config set repository.url <your-repo-url>`

**Template not found**: Run `c3cli sync` to update repository cache, then `c3cli list`

**Permission errors**: Ensure SSH keys are configured for private repositories

**Import errors after upgrade**: Clear cache with `rm -rf ~/.config/c3cli/repos/`