"""Dotfiles library for symlink management."""

import shutil
import logging
from pathlib import Path

from ..models.template import Template
from ..models.dotfile_link import DotfileLink

logger = logging.getLogger(__name__)


class DotfilesManager:
    """Manages dotfiles installation through symbolic links.

    This class handles the creation, verification, and management of symbolic links
    from the user's home directory to files in configuration repositories.
    """

    def __init__(self, user_home: Path | None = None):
        """Initialize the dotfiles manager.

        Args:
            user_home: User's home directory. Defaults to current user's home.
        """
        self.user_home = user_home or Path.home()
        self.logger = logger

    def install_template(
        self, template: Template, repository_path: Path, force: bool = False, dry_run: bool = False
    ) -> tuple[bool, list[DotfileLink]]:
        """Install a dotfiles template by creating symbolic links.

        Args:
            template: Template to install
            repository_path: Path to the cloned repository
            force: Whether to overwrite existing files
            dry_run: If True, only show what would be done

        Returns:
            Tuple of (success, list of created/planned links)
        """
        if not template.is_dotfiles_template():
            raise ValueError(f"Template {template.name} is not a dotfiles template")

        template_path = repository_path / "dotfiles" / template.name
        if not template_path.exists():
            raise FileNotFoundError(f"Template directory not found: {template_path}")

        links_to_create = []
        created_links = []

        # Plan all symlinks first
        for file_path in template.files:
            source = template_path / file_path
            target = self.user_home / file_path

            if not source.exists():
                self.logger.warning(f"Source file does not exist: {source}")
                continue

            link = DotfileLink(source=source, target=target, template_name=template.name)
            links_to_create.append(link)

        if dry_run:
            self.logger.info(f"DRY RUN: Would create {len(links_to_create)} symlinks for template {template.name}")
            for link in links_to_create:
                self.logger.info(f"  {link.target} -> {link.source}")
            return True, links_to_create

        # Create symlinks
        success = True
        for link in links_to_create:
            if self._create_single_symlink(link, force):
                created_links.append(link)
            else:
                success = False

        self.logger.info(f"Created {len(created_links)} symlinks for template {template.name}")
        return success, created_links

    def _create_single_symlink(self, link: DotfileLink, force: bool = False) -> bool:
        """Create a single symbolic link.

        Args:
            link: DotfileLink to create
            force: Whether to overwrite existing files

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we can create the symlink
            can_create, reason = link.can_create_symlink()
            if not can_create and not force:
                self.logger.error(f"Cannot create symlink {link.target}: {reason}")
                return False

            # Remove existing file/link if force is enabled
            if force and link.target.exists():
                if link.target.is_symlink():
                    link.target.unlink()
                elif link.target.is_file():
                    link.target.unlink()
                elif link.target.is_dir():
                    shutil.rmtree(link.target)

            # Ensure parent directory exists
            link.target.parent.mkdir(parents=True, exist_ok=True)

            # Create the symlink
            link.target.symlink_to(link.source)

            self.logger.debug(f"Created symlink: {link.target} -> {link.source}")
            return True

        except (OSError, PermissionError) as e:
            self.logger.error(f"Failed to create symlink {link.target}: {e}")
            return False

    def create_symlink(self, source: Path, target: Path, force: bool = False) -> bool:
        """Create a symbolic link from target to source.

        Args:
            source: Path to the source file/directory
            target: Path where symlink should be created
            force: Whether to overwrite existing files

        Returns:
            True if successful, False otherwise
        """
        link = DotfileLink(source=source, target=target, template_name="manual")
        return self._create_single_symlink(link, force)

    def verify_template_links(self, template: Template, repository_path: Path) -> list[DotfileLink]:
        """Verify all symlinks for a template.

        Args:
            template: Template to verify
            repository_path: Path to the cloned repository

        Returns:
            List of DotfileLink objects with verification status
        """
        if not template.is_dotfiles_template():
            return []

        template_path = repository_path / "dotfiles" / template.name
        links = []

        for file_path in template.files:
            source = template_path / file_path
            target = self.user_home / file_path

            link = DotfileLink(source=source, target=target, template_name=template.name)
            link.verify_link()
            links.append(link)

        return links

    def check_symlinks_status(self, target_directory: Path | None = None) -> list[dict]:
        """Check status of all symlinks in a directory.

        Args:
            target_directory: Directory to check. Defaults to user home.

        Returns:
            List of dictionaries with symlink status information
        """
        if target_directory is None:
            target_directory = self.user_home

        symlinks = []

        try:
            for item in target_directory.rglob("*"):
                if item.is_symlink():
                    # Try to calculate relative path, fallback to absolute path if not possible
                    try:
                        relative_path = str(item.relative_to(self.user_home))
                    except ValueError:
                        # Path is not relative to home directory (e.g., in tests)
                        relative_path = str(item)

                    status_info = {
                        "target": str(item),
                        "source": str(item.resolve()) if item.exists() else str(item.readlink()),
                        "exists": item.exists(),
                        "broken": item.is_symlink() and not item.exists(),
                        "relative_to_home": relative_path,
                    }
                    symlinks.append(status_info)
        except (OSError, PermissionError) as e:
            self.logger.error(f"Error scanning directory {target_directory}: {e}")

        return symlinks

    def remove_template_links(
        self, template: Template, repository_path: Path, dry_run: bool = False
    ) -> tuple[bool, int]:
        """Remove all symlinks created by a template.

        Args:
            template: Template whose links to remove
            repository_path: Path to the cloned repository
            dry_run: If True, only show what would be done

        Returns:
            Tuple of (success, number of links removed)
        """
        if not template.is_dotfiles_template():
            return True, 0

        links = self.verify_template_links(template, repository_path)
        removed_count = 0
        success = True

        if dry_run:
            valid_links = [link for link in links if link.is_symlink()]
            self.logger.info(f"DRY RUN: Would remove {len(valid_links)} symlinks for template {template.name}")
            for link in valid_links:
                self.logger.info(f"  {link.target}")
            return True, len(valid_links)

        for link in links:
            if link.is_symlink():
                try:
                    link.target.unlink()
                    removed_count += 1
                    self.logger.debug(f"Removed symlink: {link.target}")
                except (OSError, PermissionError) as e:
                    self.logger.error(f"Failed to remove symlink {link.target}: {e}")
                    success = False

        self.logger.info(f"Removed {removed_count} symlinks for template {template.name}")
        return success, removed_count

    def list_installed_templates(self, repository_path: Path) -> dict[str, list[DotfileLink]]:
        """List all installed dotfiles templates and their status.

        Args:
            repository_path: Path to the cloned repository

        Returns:
            Dictionary mapping template names to their DotfileLink objects
        """
        installed = {}
        dotfiles_dir = repository_path / "dotfiles"

        if not dotfiles_dir.exists():
            return installed

        # Find all potential templates by looking for symlinks that point into the repository
        for item in self.user_home.rglob("*"):
            if item.is_symlink():
                try:
                    source = item.resolve()
                    if source.is_relative_to(dotfiles_dir):
                        # Determine which template this belongs to
                        rel_path = source.relative_to(dotfiles_dir)
                        template_name = rel_path.parts[0] if rel_path.parts else "unknown"

                        if template_name not in installed:
                            installed[template_name] = []

                        link = DotfileLink(source=source, target=item, template_name=template_name)
                        link.verify_link()
                        installed[template_name].append(link)

                except (OSError, ValueError):
                    # Skip broken or invalid symlinks
                    continue

        return installed

    def expected_symlinks_for_template(self, template: Template, repository_path: Path) -> list[DotfileLink]:
        """Get expected symlinks for a template (public API).

        Args:
            template: Template to get symlinks for
            repository_path: Path to the repository

        Returns:
            List of DotfileLink objects representing expected symlinks
        """
        links = []
        template_path = repository_path / "dotfiles" / template.name

        for file_path in template.files:
            source = template_path / file_path
            target = self.user_home / file_path
            link = DotfileLink(source=source, target=target, template_name=template.name)
            links.append(link)

        return links
