"""Templates library for file copying operations."""

import shutil
import logging
from pathlib import Path

from ..models.template import Template
from ..models.project_file import ProjectFile

logger = logging.getLogger(__name__)


class TemplatesManager:
    """Manages project template application through file copying.

    This class handles copying template files to project directories for
    one-time initialization of new projects.
    """

    def __init__(self):
        """Initialize the templates manager."""
        self.logger = logger

    def apply_template(
        self,
        template: Template,
        repository_path: Path,
        target_directory: Path,
        force: bool = False,
        dry_run: bool = False,
    ) -> tuple[bool, list[ProjectFile]]:
        """Apply a project template by copying files to target directory.

        Args:
            template: Template to apply
            repository_path: Path to the cloned repository
            target_directory: Directory to copy files to
            force: Whether to overwrite existing files
            dry_run: If True, only show what would be done

        Returns:
            Tuple of (success, list of copied/planned files)
        """
        if not template.is_project_template():
            raise ValueError(f"Template {template.name} is not a project template")

        template_path = repository_path / "projects" / template.name
        if not template_path.exists():
            raise FileNotFoundError(f"Template directory not found: {template_path}")

        # Ensure target directory exists
        if not dry_run:
            target_directory.mkdir(parents=True, exist_ok=True)

        files_to_copy = []
        copied_files = []

        # Plan file operations from the single source of truth: template.files
        for file_path in template.files:
            source = template_path / file_path
            target = target_directory / file_path

            if not source.exists():
                self.logger.warning(f"Source file does not exist: {source}")
                continue

            files_to_copy.append((source, target))

        if dry_run:
            self.logger.info(f"DRY RUN: Would copy {len(files_to_copy)} files for template {template.name}")
            for source, target in files_to_copy:
                self.logger.info(f"  {source} -> {target}")
            # Create ProjectFile objects for dry run
            for source, target in files_to_copy:
                if source.exists():
                    copied_files.append(ProjectFile.create_from_copy(source, target, template.name))
            return True, copied_files

        # Copy files
        success = True
        for source, target in files_to_copy:
            project_file = self._copy_single_file(source, target, template.name, force)
            if project_file:
                copied_files.append(project_file)
            else:
                success = False

        self.logger.info(f"Copied {len(copied_files)} files for template {template.name}")
        return success, copied_files

    def _copy_single_file(
        self, source: Path, target: Path, template_name: str, force: bool = False
    ) -> ProjectFile | None:
        """Copy a single file from source to target.

        Args:
            source: Source file path
            target: Target file path
            template_name: Name of the template
            force: Whether to overwrite existing files

        Returns:
            ProjectFile object if successful, None otherwise
        """
        try:
            # Check if target exists and we shouldn't overwrite
            if target.exists() and not force:
                self.logger.error(f"Target file exists and force not specified: {target}")
                return None

            # Ensure parent directory exists
            target.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(source, target)

            # Create ProjectFile record
            project_file = ProjectFile.create_from_copy(source, target, template_name)

            self.logger.debug(f"Copied file: {source} -> {target}")
            return project_file

        except (OSError, PermissionError) as e:
            self.logger.error(f"Failed to copy file {source} to {target}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error copying {source}: {e}")
            return None

    def copy_template(self, source_dir: Path, target_dir: Path, exclude_patterns: list[str] | None = None) -> bool:
        """Copy entire template directory to target directory.

        Args:
            source_dir: Source template directory
            target_dir: Target directory to copy to
            exclude_patterns: Patterns of files/directories to exclude

        Returns:
            True if successful, False otherwise
        """
        if not source_dir.exists() or not source_dir.is_dir():
            self.logger.error(f"Source directory does not exist: {source_dir}")
            return False

        exclude_patterns = exclude_patterns or ["*.pyc", "__pycache__", ".git", ".DS_Store"]

        try:
            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy all files and subdirectories
            for item in source_dir.rglob("*"):
                if item.is_file():
                    # Check if file should be excluded
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if item.match(pattern) or any(part.startswith(".") and part != "." for part in item.parts):
                            should_exclude = True
                            break

                    if not should_exclude:
                        rel_path = item.relative_to(source_dir)
                        target_file = target_dir / rel_path

                        # Ensure parent directory exists
                        target_file.parent.mkdir(parents=True, exist_ok=True)

                        # Copy file with metadata
                        shutil.copy2(item, target_file)

            self.logger.info(f"Successfully copied template from {source_dir} to {target_dir}")
            return True

        except (OSError, PermissionError) as e:
            self.logger.error(f"Failed to copy template: {e}")
            return False

    def verify_copied_files(self, copied_files: list[ProjectFile]) -> list[ProjectFile]:
        """Verify integrity of copied files.

        Args:
            copied_files: List of ProjectFile objects to verify

        Returns:
            List of ProjectFile objects with updated verification status
        """
        for project_file in copied_files:
            project_file.verify_integrity()

        return copied_files

    def check_file_conflicts(
        self, template: Template, repository_path: Path, target_directory: Path
    ) -> list[tuple[Path, Path]]:
        """Check for potential file conflicts before applying template.

        Args:
            template: Template to check
            repository_path: Path to the cloned repository
            target_directory: Target directory to check

        Returns:
            List of (source, target) tuples where conflicts exist
        """
        if not template.is_project_template():
            return []

        template_path = repository_path / "projects" / template.name
        if not template_path.exists():
            return []

        conflicts = []

        # Check explicit files
        for file_path in template.files:
            source = template_path / file_path
            target = target_directory / file_path

            if source.exists() and target.exists():
                conflicts.append((source, target))

        # Only consider files declared in template.files
        # Additional files not listed are intentionally ignored

        return conflicts

    def get_template_size(self, template: Template, repository_path: Path) -> int:
        """Calculate total size of template files in bytes.

        Args:
            template: Template to analyze
            repository_path: Path to the cloned repository

        Returns:
            Total size in bytes, 0 if template not found
        """
        if not template.is_project_template():
            return 0

        template_path = repository_path / "projects" / template.name
        if not template_path.exists():
            return 0

        total_size = 0

        try:
            for item in template_path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except (OSError, PermissionError):
            pass

        return total_size

    def list_template_files(self, template: Template, repository_path: Path) -> list[Path]:
        """List all files that would be copied by a template.

        Args:
            template: Template to analyze
            repository_path: Path to the cloned repository

        Returns:
            List of file paths relative to template directory
        """
        if not template.is_project_template():
            return []

        template_path = repository_path / "projects" / template.name
        if not template_path.exists():
            return []

        files = []

        try:
            for item in template_path.rglob("*"):
                if item.is_file() and item.name not in ["metadata.toml", "install.sh"]:
                    rel_path = item.relative_to(template_path)
                    files.append(rel_path)
        except (OSError, PermissionError):
            pass

        return sorted(files)
