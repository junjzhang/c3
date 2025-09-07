"""Git operations library for repository management."""

import shutil
import logging
from pathlib import Path
from datetime import datetime

import tomllib
from git import Repo, GitCommandError, InvalidGitRepositoryError
from pydantic import ValidationError

from .command_base import RepositoryError
from ..models.template import Template, TemplateType

logger = logging.getLogger(__name__)


class GitOperationError(Exception):
    """Custom exception for Git operation errors."""

    pass


class GitOperations:
    """Handles Git repository operations for configuration management.

    This class provides methods for cloning, syncing, and discovering
    templates in Git repositories.
    """

    def __init__(self):
        """Initialize Git operations manager."""
        self.logger = logger

    def clone_repository(self, repo_url: str, local_path: str | Path, branch: str = "main") -> bool:
        """Clone a Git repository to local path.

        Args:
            repo_url: Git repository URL
            local_path: Local directory to clone to
            branch: Branch to checkout

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to Path object if needed
            if isinstance(local_path, str):
                local_path = Path(local_path)

            # Remove existing directory if it exists
            if local_path.exists():
                shutil.rmtree(local_path)

            # Ensure parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Clone the repository
            self.logger.info(f"Cloning repository {repo_url} to {local_path}")
            _ = Repo.clone_from(repo_url, local_path, branch=branch)

            self.logger.info(f"Successfully cloned repository to {local_path}")
            return True

        except GitCommandError as e:
            self.logger.error(f"Git command error while cloning {repo_url}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while cloning {repo_url}: {e}")
            return False

    def ensure_repo(self, repo_url: str, branch: str, cache_dir: Path, force: bool = False) -> Path:
        """Ensure repository is available locally, clone if missing, sync if exists.

        This eliminates the if/else branch pattern across all CLI commands.

        Args:
            repo_url: Git repository URL
            branch: Branch to sync
            cache_dir: Local cache directory path
            force: Force sync, overwriting local changes

        Returns:
            Path to the local repository

        Raises:
            RepositoryError: If clone or sync operation fails
        """
        if not cache_dir.exists():
            # Clone repository
            success = self.clone_repository(repo_url, cache_dir, branch)
            if not success:
                raise RepositoryError("Failed to clone repository")
        else:
            # Sync existing repository
            success = self.sync_repository(cache_dir, branch, force=force)
            if not success:
                raise RepositoryError("Failed to sync repository")

        return cache_dir

    def sync_repository(self, local_path: Path, branch: str | None = None, force: bool = False) -> bool:
        """Sync local repository with remote.

        Args:
            local_path: Path to local repository
            branch: Branch to sync (defaults to current branch)
            force: If True, reset local changes to match remote

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._is_valid_repo(local_path):
                self.logger.error(f"Invalid Git repository: {local_path}")
                return False

            repo = Repo(local_path)

            # Switch to specified branch if provided
            if branch and repo.active_branch.name != branch:
                try:
                    repo.git.checkout(branch)
                except GitCommandError:
                    # Branch might not exist locally, try to create it
                    try:
                        repo.git.checkout("-b", branch, f"origin/{branch}")
                    except GitCommandError as e:
                        self.logger.error(f"Failed to checkout branch {branch}: {e}")
                        return False

            # Fetch latest changes
            self.logger.info(f"Syncing repository at {local_path}")
            origin = repo.remotes.origin
            origin.fetch()

            # Handle local changes based on force option
            if force:
                # Reset to match remote (discards local changes)
                current_branch = repo.active_branch.name
                repo.git.reset("--hard", f"origin/{current_branch}")
            else:
                # Try to pull changes (may fail if conflicts exist)
                origin.pull()

            self.logger.info("Successfully synced repository")
            return True

        except GitCommandError as e:
            self.logger.error(f"Git command error while syncing: {e}")
            return False
        except InvalidGitRepositoryError:
            self.logger.error(f"Not a valid Git repository: {local_path}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while syncing: {e}")
            return False

    def get_repository_status(self, local_path: Path) -> dict | None:
        """Get status information about a Git repository.

        Args:
            local_path: Path to local repository

        Returns:
            Dictionary with repository status information, None if error
        """
        try:
            if not self._is_valid_repo(local_path):
                return None

            repo = Repo(local_path)

            # Get basic info
            status = {
                "path": str(local_path),
                "branch": repo.active_branch.name,
                "remote_url": repo.remotes.origin.url if repo.remotes else None,
                "last_commit": {
                    "hash": repo.head.commit.hexsha,
                    "message": repo.head.commit.message.strip(),
                    "author": str(repo.head.commit.author),
                    "date": datetime.fromtimestamp(repo.head.commit.committed_date).isoformat(),
                },
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files,
            }

            # Check if remote tracking branch exists and get ahead/behind info
            try:
                tracking_branch = repo.active_branch.tracking_branch()
                if tracking_branch:
                    ahead, behind = repo.git.rev_list(
                        "--count", "--left-right", f"{tracking_branch}...{repo.active_branch}"
                    ).split("\t")
                    status["ahead"] = int(ahead)
                    status["behind"] = int(behind)
            except (GitCommandError, AttributeError):
                status["ahead"] = 0
                status["behind"] = 0

            return status

        except Exception as e:
            self.logger.error(f"Error getting repository status: {e}")
            return None

    def discover_templates(self, repository_path: Path | str) -> list[Template]:
        """Discover all templates in a repository.

        Args:
            repository_path: Path to the cloned repository

        Returns:
            List of discovered Template objects
        """
        # Convert to Path object if needed
        if isinstance(repository_path, str):
            repository_path = Path(repository_path)

        templates = []

        # Discover dotfiles templates
        dotfiles_dir = repository_path / "dotfiles"
        if dotfiles_dir.exists():
            templates.extend(self._discover_templates_in_directory(dotfiles_dir, TemplateType.DOTFILES))

        # Discover project templates
        projects_dir = repository_path / "projects"
        if projects_dir.exists():
            templates.extend(self._discover_templates_in_directory(projects_dir, TemplateType.PROJECT))

        self.logger.info(f"Discovered {len(templates)} templates in repository")
        return templates

    def get_template_by_name(
        self,
        repository_path: Path | str,
        name: str,
        template_type: TemplateType | None = None,
    ) -> Template:
        """Discover and return a template by name, optionally filtered by type.

        Args:
            repository_path: Path to the cloned repository
            name: Template name to find
            template_type: Optional TemplateType to restrict search

        Returns:
            Template instance when found

        Raises:
            ConfigurationError: When template is not found
        """
        from .command_base import ConfigurationError

        templates = self.discover_templates(repository_path)
        if template_type is not None:
            if template_type == TemplateType.DOTFILES:
                templates = [t for t in templates if t.is_dotfiles_template()]
            elif template_type == TemplateType.PROJECT:
                templates = [t for t in templates if t.is_project_template()]

        by_name = {t.name: t for t in templates}
        if name in by_name:
            return by_name[name]

        raise ConfigurationError(f"Template '{name}' not found")

    def _discover_templates_in_directory(self, base_dir: Path, template_type: TemplateType) -> list[Template]:
        """Discover templates in a specific directory.

        Args:
            base_dir: Base directory to search (dotfiles/ or projects/)
            template_type: Type of templates to look for

        Returns:
            List of Template objects
        """
        templates = []

        try:
            for item in base_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    template = self._create_template_from_directory(item, template_type)
                    if template:
                        templates.append(template)
        except (OSError, PermissionError) as e:
            self.logger.error(f"Error scanning directory {base_dir}: {e}")

        return templates

    def _create_template_from_directory(self, template_dir: Path, template_type: TemplateType) -> Template | None:
        """Create a Template object from a directory.

        Args:
            template_dir: Directory containing template files
            template_type: Type of template

        Returns:
            Template object if valid, None otherwise
        """
        try:
            template_name = template_dir.name

            # Find all files in template (excluding metadata and install script)
            files = []
            install_script = None

            for item in template_dir.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(template_dir)

                    if rel_path.name == "install.sh":
                        install_script = str(rel_path)
                    elif rel_path.name != "metadata.toml":
                        files.append(str(rel_path))

            if not files:
                self.logger.debug(f"Skipping empty template directory: {template_dir}")
                return None

            # Load metadata if available
            metadata = {}
            description = f"Template {template_name}"

            metadata_file = template_dir / "metadata.toml"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "rb") as f:
                        metadata = tomllib.load(f)
                    description = metadata.get("description", description)
                except Exception as e:
                    self.logger.warning(f"Failed to parse metadata for {template_name}: {e}")

            # Create template object
            template = Template(
                name=template_name,
                description=description,
                type=template_type,
                files=files,
                install_script=install_script,
                metadata=metadata,
                discovered_at=datetime.now(),
                template_path=template_dir,
            )

            return template

        except ValidationError as e:
            self.logger.error(f"Invalid template at {template_dir}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating template from {template_dir}: {e}")
            return None

    def _is_valid_repo(self, path: Path) -> bool:
        """Check if path contains a valid Git repository.

        Args:
            path: Path to check

        Returns:
            True if valid Git repository, False otherwise
        """
        try:
            repo = Repo(path)
            return not repo.bare
        except (InvalidGitRepositoryError, GitCommandError):
            return False

    def get_remote_branches(self, repository_path: Path) -> list[str]:
        """Get list of remote branches.

        Args:
            repository_path: Path to local repository

        Returns:
            List of remote branch names
        """
        try:
            if not self._is_valid_repo(repository_path):
                return []

            repo = Repo(repository_path)
            origin = repo.remotes.origin
            origin.fetch()

            branches = []
            for ref in origin.refs:
                if ref.name.startswith("origin/"):
                    branch_name = ref.name[7:]  # Remove 'origin/' prefix
                    if branch_name != "HEAD":
                        branches.append(branch_name)

            return sorted(branches)

        except Exception as e:
            self.logger.error(f"Error getting remote branches: {e}")
            return []

    def validate_repository_structure(self, repository_path: Path) -> tuple[bool, list[str]]:
        """Validate that repository has expected structure for c3cli.

        Args:
            repository_path: Path to repository to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if not self._is_valid_repo(repository_path):
            issues.append("Not a valid Git repository")
            return False, issues

        # Check for expected directories
        dotfiles_dir = repository_path / "dotfiles"
        projects_dir = repository_path / "projects"

        if not dotfiles_dir.exists() and not projects_dir.exists():
            issues.append("Repository must contain 'dotfiles' or 'projects' directory")

        # Validate template directories
        for template_dir in [dotfiles_dir, projects_dir]:
            if template_dir.exists():
                try:
                    for item in template_dir.iterdir():
                        if item.is_dir() and not item.name.startswith("."):
                            # Check if template has any files
                            has_files = any(f.is_file() for f in item.rglob("*"))
                            if not has_files:
                                issues.append(f"Empty template directory: {item.relative_to(repository_path)}")
                except (OSError, PermissionError):
                    issues.append(f"Cannot access directory: {template_dir.relative_to(repository_path)}")

        return len(issues) == 0, issues
