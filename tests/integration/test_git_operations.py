"""Integration tests for Git repository operations.

These tests verify Git operations work correctly with real repositories.
Tests MUST FAIL initially (TDD).
"""

import tempfile
from pathlib import Path

from git import Repo


class TestGitOperationsIntegration:
    """Test Git repository operations integration."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.temp_repo_dir = tempfile.mkdtemp()
        self.temp_clone_dir = tempfile.mkdtemp()

    def test_can_clone_repository(self):
        """Test that we can clone a Git repository."""
        # Create a test repository
        repo = Repo.init(self.temp_repo_dir)

        # Add some content
        test_file = Path(self.temp_repo_dir) / "README.md"
        test_file.write_text("# Test Repository")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Test cloning (this will fail until git_ops is implemented)
        from src.lib.git_ops import GitOperations

        git_ops = GitOperations()

        success = git_ops.clone_repository(self.temp_repo_dir, self.temp_clone_dir)
        assert success

        cloned_readme = Path(self.temp_clone_dir) / "README.md"
        assert cloned_readme.exists()
        assert cloned_readme.read_text() == "# Test Repository"

    def test_can_sync_repository_changes(self):
        """Test that we can sync repository changes."""
        # This will fail until implementation
        from src.lib.git_ops import GitOperations

        git_ops = GitOperations()

        # Initial clone
        repo = Repo.init(self.temp_repo_dir)
        test_file = Path(self.temp_repo_dir) / "config.txt"
        test_file.write_text("version 1")
        repo.index.add(["config.txt"])
        repo.index.commit("Version 1")

        git_ops.clone_repository(self.temp_repo_dir, self.temp_clone_dir)

        # Make changes to original repository
        test_file.write_text("version 2")
        repo.index.add(["config.txt"])
        repo.index.commit("Version 2")

        # Sync changes
        success = git_ops.sync_repository(self.temp_clone_dir)
        assert success

        synced_file = Path(self.temp_clone_dir) / "config.txt"
        assert synced_file.read_text() == "version 2"

    def test_can_check_repository_status(self):
        """Test that we can check repository status."""
        from src.lib.git_ops import GitOperations

        git_ops = GitOperations()

        # Create and clone repository
        repo = Repo.init(self.temp_repo_dir)
        test_file = Path(self.temp_repo_dir) / "test.txt"
        test_file.write_text("content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        git_ops.clone_repository(self.temp_repo_dir, self.temp_clone_dir)

        # Check status
        status = git_ops.get_repository_status(self.temp_clone_dir)
        assert status is not None
        assert "branch" in status
        assert "last_commit" in status

    def test_discovers_templates_in_repository(self):
        """Test that we can discover templates in repository structure."""
        from src.lib.git_ops import GitOperations

        git_ops = GitOperations()

        # Create repository with template structure
        repo = Repo.init(self.temp_repo_dir)

        # Create dotfiles templates
        dotfiles_dir = Path(self.temp_repo_dir) / "dotfiles"
        vim_template = dotfiles_dir / "vim-config"
        vim_template.mkdir(parents=True)
        (vim_template / ".vimrc").write_text("set number")
        (vim_template / "metadata.toml").write_text('description = "Vim config"')

        # Create projects templates
        projects_dir = Path(self.temp_repo_dir) / "projects"
        python_template = projects_dir / "python-app"
        python_template.mkdir(parents=True)
        (python_template / "main.py").write_text('print("hello")')

        repo.index.add(
            ["dotfiles/vim-config/.vimrc", "dotfiles/vim-config/metadata.toml", "projects/python-app/main.py"]
        )
        repo.index.commit("Add templates")

        git_ops.clone_repository(self.temp_repo_dir, self.temp_clone_dir)

        # Discover templates
        templates = git_ops.discover_templates(self.temp_clone_dir)
        assert len(templates) >= 2

        template_names = [t.name for t in templates]
        assert "vim-config" in template_names
        assert "python-app" in template_names

    def test_handles_authentication_errors(self):
        """Test handling of Git authentication errors."""
        from src.lib.git_ops import GitOperations

        git_ops = GitOperations()

        # Try to clone from invalid repository
        success = git_ops.clone_repository("https://invalid-url.git", self.temp_clone_dir)
        assert not success

    def test_handles_network_errors(self):
        """Test handling of network errors during Git operations."""
        from src.lib.git_ops import GitOperations

        git_ops = GitOperations()

        # Try to clone from unreachable repository
        success = git_ops.clone_repository("git://unreachable-host/repo.git", self.temp_clone_dir)
        assert not success
