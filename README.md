# c3cli

Claude Code Configuration Manager CLI

A simple CLI tool for managing dotfiles (symlinks) and project templates (file copying) from Git repositories.

## Features

- **Dotfiles Management**: Create symbolic links to configuration files in your home directory
- **Project Templates**: Copy template files to initialize new projects
- **Install Scripts**: Support for optional install.sh scripts in templates
- **Git Integration**: Sync templates from remote Git repositories

## Commands

- `c3cli install <template>` - Apply dotfiles template (creates symlinks)
- `c3cli apply <template>` - Apply project template (copies files)
- `c3cli list [pattern]` - List available templates
- `c3cli sync` - Update repository cache
- `c3cli status` - Show installation status
- `c3cli config` - Manage configuration

## Installation

## Shell Completion

c3cli ships with Click/Typer completion. You can enable it per-shell:

- Bash
  - Temporary (current session): `c3cli --show-completion >> /dev/stdout && source <(c3cli --show-completion)`
  - Persistent (Linux): `c3cli --install-completion`

- Zsh
  - Ensure `compinit` is enabled in your shell config.
  - Temporary: `source <(c3cli --show-completion)`
  - Persistent: `c3cli --install-completion`

- Fish
  - Temporary: `c3cli --show-completion | source`
  - Persistent: `c3cli --install-completion`

If your environment manages dotfiles differently, you can also capture the script explicitly:

```
c3cli --show-completion > ~/.config/c3cli/completion.sh
source ~/.config/c3cli/completion.sh
```

Note: Completion requires c3cli 0.1.0+ and is enabled by default in the CLI.

```bash
pixi install
```

## Quick Start

### 1. Configure Your Repository

First, you need to configure a Git repository containing your dotfiles and project templates:

```bash
# Set your configuration repository URL
c3cli config set repository.url https://github.com/your/dotfiles-repo

# Optional: set a different branch (default: main)
c3cli config set repository.branch develop

# Verify configuration
c3cli config show
```

### 2. Repository Structure

Your configuration repository should follow this structure:

```
your-dotfiles-repo/
├── dotfiles/           # Symlink templates (dotfiles)
│   ├── vim/            # Template name: "vim"
│   │   ├── .vimrc      # → symlinked to ~/.vimrc
│   │   └── .vim/       # → symlinked to ~/.vim/
│   │       └── plugins/
│   └── zsh/            # Template name: "zsh"  
│       ├── .zshrc      # → symlinked to ~/.zshrc
│       ├── .zsh/       # → symlinked to ~/.zsh/
│       └── config/     # → symlinked to ~/config/
│           └── .zshenv
└── projects/           # Copy templates (project scaffolds)
    ├── python-project/ # Template name: "python-project"
    │   ├── pyproject.toml    # → copied to ./pyproject.toml
    │   ├── src/             # → copied to ./src/
    │   │   └── __init__.py
    │   ├── tests/           # → copied to ./tests/
    │   ├── README.md        # → copied to ./README.md
    │   └── install.sh       # Optional setup script
    └── react-app/      # Template name: "react-app"
        ├── package.json     # → copied to ./package.json
        ├── src/            # → copied to ./src/
        ├── public/         # → copied to ./public/
        └── metadata.toml   # Optional template metadata
```

### File Mapping Rules

#### Dotfiles (Symlinks)
**Individual files** (leaf nodes) in `dotfiles/<template>/` are symlinked to your home directory preserving the **exact path structure**:

```bash
# Repository structure
dotfiles/vim/.vimrc              → ~/.vimrc
dotfiles/vim/.vim/plugins/       → ~/.vim/plugins/  
dotfiles/zsh/.zshrc              → ~/.zshrc
dotfiles/zsh/config/.zshenv      → ~/config/.zshenv

# Precise .config subdirectory control
dotfiles/nvim/.config/nvim/      → ~/.config/nvim/
dotfiles/alacritty/.config/alacritty/ → ~/.config/alacritty/
dotfiles/tmux/.config/tmux/      → ~/.config/tmux/
```

#### Project Templates (File Copy)
Files in `projects/<template>/` are copied to the current/target directory preserving the **exact path structure**:

```bash
# Repository structure  
projects/python-project/pyproject.toml    → ./pyproject.toml
projects/python-project/src/__init__.py   → ./src/__init__.py
projects/python-project/tests/            → ./tests/
```

#### Special Files
- `metadata.toml` - Template metadata (not copied/linked)  
- `install.sh` - Optional post-installation script (not copied/linked)

### Precise .config Directory Control

A common use case is syncing only specific subdirectories within `.config/`. Here's how to structure your repository for precise control:

```bash
# Repository structure for .config management
your-dotfiles-repo/
└── dotfiles/
    ├── nvim/                    # Template: "nvim"
    │   └── .config/
    │       └── nvim/
    │           ├── init.lua     # → ~/.config/nvim/init.lua
    │           ├── lua/         # → ~/.config/nvim/lua/
    │           └── after/       # → ~/.config/nvim/after/
    ├── alacritty/               # Template: "alacritty" 
    │   └── .config/
    │       └── alacritty/
    │           ├── alacritty.yml    # → ~/.config/alacritty/alacritty.yml
    │           └── themes/          # → ~/.config/alacritty/themes/
    └── tmux/                    # Template: "tmux"
        └── .config/
            └── tmux/
                ├── tmux.conf    # → ~/.config/tmux/tmux.conf
                └── plugins/     # → ~/.config/tmux/plugins/
```

**Usage Examples:**

```bash
# Install only Neovim config (not entire .config)
c3cli install nvim       # Creates ~/.config/nvim/ symlinks only

# Install only Alacritty config  
c3cli install alacritty  # Creates ~/.config/alacritty/ symlinks only

# Install multiple specific configs
c3cli install nvim
c3cli install alacritty
c3cli install tmux

# List what's available
c3cli list --type dotfiles
```

**Benefits:**
- ✅ **Selective sync**: Only sync the configs you need
- ✅ **Modular management**: Each app config is independent  
- ✅ **No conflicts**: Won't override other .config subdirectories
- ✅ **Clean organization**: Each template focuses on one tool

### Important: File-Level Symlinks

**c3cli creates symlinks for individual files (leaf nodes), not directories:**

```bash
# What actually gets created:
~/.config/nvim/init.lua        → [symlink to repo]/dotfiles/nvim/.config/nvim/init.lua
~/.config/nvim/lua/plugins.lua → [symlink to repo]/dotfiles/nvim/.config/nvim/lua/plugins.lua

# NOT a single directory symlink:
~/.config/nvim/ → [symlink to repo]/dotfiles/nvim/.config/nvim/  # ❌ This doesn't happen
```

**Why file-level symlinks?**
- ✅ **Safer**: Won't overwrite existing directories
- ✅ **Granular control**: Each file can be managed independently  
- ✅ **Mixed sources**: You can have files from different templates in the same directory
- ✅ **Backup friendly**: Existing files are preserved (with `--force` option)

**Result**: Directory structure is created automatically, but only individual files are symlinked.

### Advanced Configuration

#### Template Metadata (metadata.toml)

Add a `metadata.toml` file to provide additional information about your template:

```toml
# Example: dotfiles/vim/metadata.toml
description = "Vim configuration with plugins and custom settings"
version = "2.1.0"
author = "Your Name"
tags = ["editor", "vim", "development"]

[dependencies]
system = ["vim", "git"]
optional = ["fzf", "ripgrep"]

[notes]
installation = "Run :PlugInstall after installation"
```

#### Install Scripts (install.sh)

Add executable setup scripts for additional configuration:

```bash
#!/bin/bash
# Example: projects/python-project/install.sh

echo "Setting up Python project..."

# Install dependencies
pip install -r requirements.txt

# Initialize git repo
git init
git add .
git commit -m "Initial commit"

# Setup pre-commit hooks
pre-commit install

echo "Python project setup complete!"
```

### 3. Use Templates

Once configured, you can:

```bash
# List all available templates
c3cli list

# Install dotfiles (creates symlinks to your home directory)
c3cli install vim

# Apply project template (copies files to current directory)
c3cli apply python-project

# Check installation status
c3cli status
```

## Configuration Repository Examples

- **Dotfiles repositories**: Store configuration files like `.vimrc`, `.zshrc`, etc.
- **Project templates**: Starter templates for new projects
- **Install scripts**: Optional `install.sh` scripts for additional setup

### Supported Git URLs

```bash
# HTTPS
c3cli config set repository.url https://github.com/user/repo.git

# SSH  
c3cli config set repository.url git@github.com:user/repo.git

# Git protocol
c3cli config set repository.url git://github.com/user/repo.git
```

## Configuration Management

### View Configuration

```bash
# Show current configuration
c3cli config show

# List all configuration options
c3cli config list

# Get specific configuration value
c3cli config get repository.url
c3cli config get repository.branch
```

### Available Configuration Keys

| Key | Description | Default |
|-----|-------------|---------|
| `repository.url` | Git repository URL containing templates | *None* (required) |
| `repository.branch` | Git branch to use | `main` |

### Troubleshooting

**Error: "No repository configured"**
```bash
# Fix by setting a repository URL
c3cli config set repository.url https://github.com/your/dotfiles-repo
```

**Error: "Template not found"**
```bash
# List available templates
c3cli list

# Make sure your repository has the correct structure
c3cli sync  # Update repository cache
```

**Error: "Failed to clone repository"**
```bash
# Check if repository URL is accessible
# Verify SSH keys or authentication for private repos
c3cli config get repository.url
```

## Complete Example Workflow

### 1. Create Your Dotfiles Repository

```bash
# Create a new repository
mkdir my-dotfiles && cd my-dotfiles
git init

# Create dotfiles structure
mkdir -p dotfiles/vim dotfiles/zsh dotfiles/nvim/.config/nvim
mkdir -p projects/python-project projects/node-app

# Add traditional dotfiles
echo 'set number' > dotfiles/vim/.vimrc
echo 'export PATH=$HOME/bin:$PATH' > dotfiles/zsh/.zshrc

# Add .config-based configurations
cat > dotfiles/nvim/.config/nvim/init.lua << 'EOF'
-- Neovim configuration
vim.opt.number = true
vim.opt.relativenumber = true
EOF

mkdir -p dotfiles/nvim/.config/nvim/lua
echo 'return {}' > dotfiles/nvim/.config/nvim/lua/plugins.lua

# Add project templates
echo '{"name": "my-app", "version": "1.0.0"}' > projects/node-app/package.json
cat > projects/python-project/pyproject.toml << 'EOF'
[project]
name = "my-project"
version = "0.1.0"
dependencies = []
EOF

# Commit and push
git add .
git commit -m "Initial dotfiles and templates"
git remote add origin https://github.com/yourusername/my-dotfiles.git
git push -u origin main
```

### 2. Configure c3cli

```bash
# Configure your dotfiles repository
c3cli config set repository.url https://github.com/yourusername/my-dotfiles.git

# Verify everything is working
c3cli config show
c3cli list
```

### 3. Use Your Templates

```bash
# Install dotfiles (creates symlinks)
c3cli install vim    # Creates ~/.vimrc symlink
c3cli install zsh    # Creates ~/.zshrc symlink

# Create a new project
mkdir my-new-project && cd my-new-project
c3cli apply python-project  # Copies template files

# Check what's installed
c3cli status
```
