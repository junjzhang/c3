# Quickstart Guide: Claude Code Configuration Manager CLI

## Overview
The Claude Code Configuration Manager CLI (`c3cli`) is a simple tool for managing dotfiles and project templates from Git repositories.

## Installation

### Prerequisites
- Python 3.11+
- Git
- Pixi (for development)

### Install from source
```bash
git clone <repository-url>
cd c3cli
pixi install
pixi run c3cli --help
```

## First Run Setup

### 1. Configure your repository
```bash
# Set your config repository URL
c3cli config set repository.url https://github.com/your-username/config-repo

# Verify configuration
c3cli config list
```

### 2. Sync with repository
```bash
# Download templates from your config repo
c3cli sync

# List available templates
c3cli list
```

## Basic Usage

### Managing Dotfiles (Global Configuration)

**Install dotfiles template** (creates symlinks):
```bash
# Install vim configuration
c3cli install vim-config

# Output:
# Installing dotfiles template: vim-config
# ✓ ~/.vimrc -> /path/to/repo/dotfiles/vim-config/.vimrc
# ✓ ~/.vim/ -> /path/to/repo/dotfiles/vim-config/.vim/
# ? Run install.sh script? [y/N] y
# ✓ Executed install.sh successfully
# Template 'vim-config' installed successfully
```

**Check status of installed dotfiles**:
```bash
c3cli status

# Output:
# Repository: https://github.com/user/config-repo (up to date)
# Last sync: 2025-09-07 14:30:00
# 
# Installed dotfiles:
#   vim-config    ✓ 3 files linked
#   shell-setup   ✓ 5 files linked
```

### Managing Project Templates

**Apply project template** (copies files):
```bash
# Navigate to your project directory
mkdir my-python-project && cd my-python-project

# Apply Python project template
c3cli apply python-project

# Output:
# Applying project template: python-project
# ✓ pyproject.toml copied
# ✓ src/ directory copied  
# ✓ tests/ directory copied
# ? Run install.sh script? [y/N] y
# ✓ Executed install.sh successfully
# Template 'python-project' applied to current directory
```

## Repository Structure

Your configuration repository should follow this structure:

```
config-repo/
├── dotfiles/                 # Global user configurations
│   ├── vim-config/
│   │   ├── .vimrc
│   │   ├── .vim/
│   │   ├── install.sh        # Optional dependency installer
│   │   └── metadata.toml     # Optional template metadata
│   └── shell-setup/
│       ├── .bashrc
│       ├── .aliases
│       └── install.sh
└── projects/                 # Project templates  
    ├── python-project/
    │   ├── pyproject.toml
    │   ├── src/
    │   ├── tests/
    │   ├── .gitignore
    │   ├── install.sh
    │   └── metadata.toml
    └── node-app/
        ├── package.json
        ├── src/
        └── install.sh
```

### Template Metadata (Optional)

Create `metadata.toml` in each template directory:

```toml
name = "Python Project Template"
description = "Modern Python project with pytest, black, and mypy"
author = "Your Name"
version = "1.0.0"

[requirements]
os = ["linux", "macos"]
min_version = "0.1.0"

tags = ["python", "testing", "formatting"]
```

### Install Scripts (Optional)

Create `install.sh` for dependency installation:

```bash
#!/bin/bash
# install.sh for python-project template

echo "Installing Python development tools..."
pip install --user black mypy pytest
echo "✓ Python tools installed"
```

## Common Workflows

### Daily Development Setup
```bash
# 1. Sync latest templates
c3cli sync

# 2. Install/update your dotfiles
c3cli install vim-config
c3cli install shell-setup

# 3. Check everything is working
c3cli status
```

### Starting New Projects
```bash
# 1. Create project directory
mkdir my-new-project && cd my-new-project

# 2. See available project templates
c3cli list --type project

# 3. Apply appropriate template
c3cli apply python-project
# or
c3cli apply node-app

# 4. Customize as needed
```

### Maintaining Templates
```bash
# 1. Update your config repository
# (edit files in your Git repo)

# 2. Sync changes locally
c3cli sync

# 3. Re-install dotfiles to get updates
c3cli install vim-config --force

# 4. Verify updates
c3cli status
```

## Advanced Usage

### Multiple Configuration Repositories
```bash
# Use different repo for this command
c3cli --repo https://github.com/team/shared-configs list

# Apply template from different repo  
c3cli --repo https://github.com/company/templates apply corporate-setup
```

### Dry Run Mode
```bash
# See what would be done without executing
c3cli install vim-config --dry-run
c3cli apply python-project --dry-run
```

### Force Overwrite
```bash
# Overwrite existing files without prompting
c3cli install vim-config --force
c3cli apply python-project --force
```

### Skip Install Scripts
```bash
# Don't prompt to run install.sh
c3cli install vim-config --no-script
c3cli apply python-project --no-script
```

## Troubleshooting

### Common Issues

**Template not found:**
```bash
c3cli list  # Check available templates
c3cli sync  # Make sure you're up to date
```

**File conflicts:**
```bash
# Back up existing file and try again
mv ~/.vimrc ~/.vimrc.backup
c3cli install vim-config
```

**Permission errors:**
```bash
# Check directory permissions
ls -la ~/.config/c3cli/
# Make sure you can write to target directories
```

**Repository access issues:**
```bash
# Test Git access
git clone https://github.com/your-username/config-repo /tmp/test
# Check SSH key setup for private repos
```

### Debug Mode
```bash
# Enable verbose logging
c3cli --verbose sync
c3cli --verbose install vim-config
```

### Configuration Issues
```bash
# Show current configuration
c3cli config list

# Reset configuration to defaults
rm ~/.config/c3cli/config.toml
c3cli config list  # Will recreate with defaults
```

## Integration Examples

### CI/CD Environment Setup
```bash
#!/bin/bash
# setup-dev-environment.sh

# Install c3cli
pixi install c3cli

# Configure repository
c3cli config set repository.url $CONFIG_REPO_URL

# Install development environment
c3cli sync
c3cli install dev-tools --no-script  # Skip interactive scripts in CI
c3cli apply ci-project --force       # Overwrite if exists
```

### Team Onboarding Script
```bash
#!/bin/bash
# onboard-developer.sh

echo "Setting up development environment..."

# Install essential dotfiles
c3cli install shell-setup
c3cli install git-config  
c3cli install editor-config

# Show status
c3cli status

echo "Development environment ready! 🚀"
```

This tool focuses on simplicity and safety - it will always prompt before potentially destructive operations and provides clear feedback about what it's doing.