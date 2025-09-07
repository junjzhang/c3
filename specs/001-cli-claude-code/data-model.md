# Data Model: Claude Code Configuration Manager CLI

## Core Entities

### Template
Represents a configuration template that can be applied to user or project scope.

**Fields**:
- `name: str` - Unique template identifier
- `description: str` - Human-readable description of template purpose
- `type: TemplateType` - Either "dotfiles" (user scope) or "project" (repo scope)
- `files: list[str]` - List of file paths within template directory
- `install_script: Optional[str]` - Path to install.sh if present
- `metadata: dict[str, Any]` - Additional metadata from metadata.toml

**Validation Rules**:
- Name must be valid directory name (no special chars)
- Description required and non-empty
- Files list must contain at least one file
- Install script path must exist if specified

**State Transitions**:
- Template discovered → Template validated → Template applied

### ConfigRepository (Removed)
This model has been removed. Responsibility is handled by the composition of `CLIConfig` (persistent settings) and `GitOperations` (runtime Git actions). The section is kept for historical context only.

[Removed: see note above]

### DotfileLink
Represents a symlink from user directory to config repository file.

**Fields**:
- `source: Path` - Path to file in config repository
- `target: Path` - Path to symlink in user directory
- `template_name: str` - Template that created this link
- `created_at: datetime` - When symlink was created

**Validation Rules**:
- Source file must exist in repository
- Target parent directory must exist or be creatable
- Target must not conflict with existing file (unless force flag)

**State Transitions**:
- Link planned → Link created → Link verified

### ProjectFile
Represents a file copied from template to project directory.

**Fields**:
- `source: Path` - Path to file in template
- `target: Path` - Path to copied file in project
- `template_name: str` - Template that created this file
- `copied_at: datetime` - When file was copied
- `checksum: str` - SHA256 hash of copied content

**Validation Rules**:
- Source file must exist in template
- Target directory must be writable
- Checksum must match source file at copy time

**State Transitions**:
- Copy planned → Copy executed → Copy verified

### CLIConfig
Represents user's local CLI configuration.

**Fields**:
- `default_repo_url: Optional[str]` - Default config repository URL
- `repo_branch: str` - Default branch to use (default: main)
- `user_home: Path` - User's home directory path
- `config_dir: Path` - CLI configuration directory (~/.config/c3cli)
- `log_level: str` - Logging level (debug, info, warn, error)

**Validation Rules**:
- Repository URL must be valid Git URL if provided
- Branch name must be valid Git branch name
- Paths must be accessible
- Log level must be valid logging level

**State Transitions**:
- Default config → User customized → Config saved

## Data Relationships

### Template → Files
- One template contains multiple files
- Files are relative paths within template directory
- Relationship: Template.files = List[relative_path]

### ConfigRepository → Templates (Removed)
[Removed: relationships now described operationally under Git repository structure and discovery in `GitOperations`]

### Template → DotfileLinks
- One template can create multiple dotfile links
- Each link tracks its source template
- Relationship: DotfileLink.template_name → Template.name

### Template → ProjectFiles
- One template can create multiple project files
- Each file tracks its source template  
- Relationship: ProjectFile.template_name → Template.name

### ConfigRepository → Local Storage (Removed)
[Removed: local cache paths are derived by `CLIConfig.get_repo_cache_dir()` and used by `GitOperations`]

## Error States

### Template Validation Errors
- `TemplateNotFound`: Template name doesn't exist in repository
- `InvalidTemplateStructure`: Template directory missing required files
- `TemplateMetadataError`: metadata.toml parsing or validation failed

### Repository Errors
- `RepositoryNotFound`: Git repository URL not accessible
- `RepositoryCloneError`: Failed to clone repository locally
- `RepositorySyncError`: Failed to sync with remote repository
- `InvalidRepositoryStructure`: Repository doesn't contain valid templates

### File Operation Errors
- `FileConflictError`: Target file already exists and differs
- `PermissionError`: Insufficient permissions for file operation
- `SymlinkError`: Failed to create or verify symbolic link
- `CopyError`: Failed to copy file to target location

### Configuration Errors
- `ConfigValidationError`: Invalid configuration values
- `ConfigFileError`: Cannot read/write configuration file
- `HomeDirectoryError`: Cannot determine or access user home directory

## Persistence Strategy

### Configuration Files
- **User config**: `~/.config/c3cli/config.toml` - CLIConfig data
- **Repository cache**: `~/.config/c3cli/repos/` - Local repository clones
- **State tracking**: `~/.config/c3cli/state.json` - Applied templates and links

### Git Repository Structure
```
config-repo/
├── dotfiles/
│   ├── template1/
│   │   ├── .bashrc
│   │   ├── .vimrc
│   │   ├── install.sh
│   │   └── metadata.toml
│   └── template2/
│       └── ...
└── projects/
    ├── python-project/
    │   ├── pyproject.toml
    │   ├── .gitignore  
    │   ├── install.sh
    │   └── metadata.toml
    └── node-project/
        └── ...
```

### State Persistence
- Symlink tracking for cleanup and status reporting
- Copy tracking for conflict detection and reporting
- Template application history for rollback capability
