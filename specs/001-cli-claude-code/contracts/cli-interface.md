# CLI Interface Contract

## Command Structure

All commands follow the pattern: `c3cli <command> [options] [arguments]`

## Global Options

```bash
--help, -h          Show help message and exit
--version, -v       Show version and exit  
--config PATH       Path to config file (default: ~/.config/c3cli/config.toml)
--repo URL          Config repository URL (overrides config file)
--verbose           Enable verbose logging
--quiet             Suppress non-error output
--format FORMAT     Output format: text, json (default: text)
```

## Commands

### `c3cli install <template>`
Apply a dotfiles template using symbolic links.

**Arguments:**
- `template: str` - Name of template to install

**Options:**
- `--force, -f` - Overwrite existing files without prompt
- `--dry-run, -n` - Show what would be done without executing
- `--no-script` - Skip running install.sh if present

**Examples:**
```bash
c3cli install vim-config
c3cli install shell-setup --force
c3cli install python-dev --dry-run --no-script
```

**Exit Codes:**
- `0` - Success
- `1` - Template not found
- `2` - File conflict (without --force)
- `3` - Permission error
- `4` - Repository error

**Output Format:**
```
Installing dotfiles template: vim-config
✓ ~/.vimrc -> /path/to/repo/dotfiles/vim-config/.vimrc
✓ ~/.vim/ -> /path/to/repo/dotfiles/vim-config/.vim/
? Run install.sh script? [y/N] y
✓ Executed install.sh successfully
Template 'vim-config' installed successfully
```

### `c3cli apply <template>`  
Apply a project template by copying files to current directory.

**Arguments:**
- `template: str` - Name of template to apply

**Options:**
- `--target DIR` - Target directory (default: current directory)
- `--force, -f` - Overwrite existing files without prompt
- `--dry-run, -n` - Show what would be done without executing
- `--no-script` - Skip running install.sh if present

**Examples:**
```bash
c3cli apply python-project
c3cli apply node-app --target ./new-project
c3cli apply rust-cli --force --no-script
```

**Exit Codes:**
- `0` - Success
- `1` - Template not found
- `2` - File conflict (without --force)
- `3` - Permission error
- `4` - Repository error

**Output Format:**
```
Applying project template: python-project
✓ pyproject.toml copied
✓ src/ directory copied
✓ tests/ directory copied
? Run install.sh script? [y/N] y
✓ Executed install.sh successfully  
Template 'python-project' applied to current directory
```

### `c3cli list [pattern]`
List available templates.

**Arguments:**
- `pattern: str` - Optional filter pattern (glob-style)

**Options:**
- `--type TYPE` - Filter by type: dotfiles, project, all (default: all)
- `--detailed, -d` - Show detailed information including descriptions

**Examples:**
```bash
c3cli list
c3cli list python*
c3cli list --type dotfiles --detailed
```

**Exit Codes:**
- `0` - Success  
- `4` - Repository error

**Output Format:**
```
Available templates:
dotfiles/
  vim-config     - Vim editor configuration
  shell-setup    - Shell aliases and functions
projects/
  python-project - Python project with pytest setup
  node-app       - Node.js application template
```

### `c3cli sync`
Synchronize with remote configuration repository.

**Options:**
- `--branch BRANCH` - Specific branch to sync (default: configured branch)
- `--force, -f` - Force sync even if local changes exist

**Examples:**
```bash
c3cli sync
c3cli sync --branch develop
c3cli sync --force
```

**Exit Codes:**
- `0` - Success
- `4` - Repository error  
- `5` - Sync conflict

**Output Format:**
```
Syncing with repository: https://github.com/user/config-repo
✓ Fetched latest changes
✓ Updated 3 templates
Sync completed successfully
```

### `c3cli status`
Show status of installed templates and repository.

**Options:**
- `--template NAME` - Show status for specific template only

**Examples:**
```bash
c3cli status
c3cli status --template vim-config
```

**Exit Codes:**
- `0` - Success
- `4` - Repository error

**Output Format:**
```
Repository: https://github.com/user/config-repo (up to date)
Last sync: 2025-09-07 14:30:00

Installed dotfiles:
  vim-config    ✓ 3 files linked
  shell-setup   ✗ 1 broken link (~/.bashrc)

Applied projects:
  python-project  ✓ Applied to /home/user/myproject (2025-09-06)
```

### `c3cli config`
Manage CLI configuration.

**Subcommands:**
- `get <key>` - Get configuration value
- `set <key> <value>` - Set configuration value  
- `list` - List all configuration

**Examples:**
```bash
c3cli config list
c3cli config get repo_url
c3cli config set repo_url https://github.com/user/new-config-repo
```

**Exit Codes:**
- `0` - Success
- `6` - Configuration error

## Error Handling

### Error Response Format
```json
{
  "error": "TemplateNotFound",
  "message": "Template 'invalid-name' not found in repository",
  "details": {
    "template": "invalid-name",
    "available_templates": ["vim-config", "shell-setup"]
  }
}
```

### Common Error Types
- `TemplateNotFound` - Requested template doesn't exist
- `FileConflict` - Target file exists and differs from template
- `PermissionError` - Insufficient permissions for operation
- `RepositoryError` - Git repository access or sync error  
- `ConfigurationError` - Invalid configuration values
- `ScriptExecutionError` - install.sh script failed

## Configuration File Format

Location: `~/.config/c3cli/config.toml`

```toml
[repository]
url = "https://github.com/user/config-repo"
branch = "main"
local_path = "~/.config/c3cli/repos/default"

[preferences]  
log_level = "info"
default_format = "text"
auto_sync = true
prompt_for_scripts = true

[paths]
config_dir = "~/.config/c3cli"
```