"""Test fixtures for c3cli testing with dependency injection."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from git import Repo
from typer.testing import CliRunner

from src.lib.git_ops import GitOperations
from src.lib.dotfiles import DotfilesManager
from src.models.cli_config import CLIConfig


class TestWithIsolation:
    """Base test class providing isolated environments for CLI testing.

    This class provides:
    - Temporary home directory
    - Temporary config directory
    - Test repository with templates
    - Isolated CLIConfig and DotfilesManager instances
    """

    # Test repository URL - kept separate from production code
    TEST_REPO_URL = "https://github.com/junjzhang/c3-config-test.git"

    def setup_method(self):
        """Set up isolated test environment."""
        # Create temporary directories
        self.temp_home = Path(tempfile.mkdtemp(prefix="c3cli_test_home_"))
        self.temp_config = Path(tempfile.mkdtemp(prefix="c3cli_test_config_"))
        self.temp_repo_cache = self.temp_config / "repos" / "test_repo"

        # Ensure directories exist
        self.temp_config.mkdir(parents=True, exist_ok=True)
        self.temp_repo_cache.mkdir(parents=True, exist_ok=True)

        # Initialize as Git repository
        self.test_repo = Repo.init(self.temp_repo_cache)

        # Configure git user for commits
        with self.test_repo.config_writer() as git_config:
            git_config.set_value("user", "name", "Test User")
            git_config.set_value("user", "email", "test@example.com")

        # Create test configuration
        self.test_config = CLIConfig(
            default_repo_url=self.TEST_REPO_URL,
            user_home=self.temp_home,
            config_dir=self.temp_config,
            auto_sync=False,  # Disable auto-sync for testing
        )

        # Create managers with test configuration
        self.dotfiles_manager = DotfilesManager(user_home=self.temp_home)
        self.git_ops = GitOperations()

        # Create CLI runner
        self.cli_runner = CliRunner()

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temporary directories
        if self.temp_home.exists():
            shutil.rmtree(self.temp_home, ignore_errors=True)
        if self.temp_config.exists():
            shutil.rmtree(self.temp_config, ignore_errors=True)

    def create_test_template_files(self) -> Path:
        """Create a local test template structure.

        Returns:
            Path to the created template directory
        """
        # Create dotfiles template structure
        template_dir = self.temp_repo_cache / "dotfiles" / "test-template"
        template_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        (template_dir / ".vimrc").write_text('" Test vim config\nset number\nsyntax on\n')
        (template_dir / ".gitconfig").write_text("[user]\n    name = Test User\n    email = test@example.com\n")

        # Create metadata
        (template_dir / "metadata.toml").write_text("""
[template]
name = "test-template"
description = "Test template for unit testing"
type = "dotfiles"
version = "1.0.0"
""")

        # Add and commit files to Git repository
        self.test_repo.index.add(
            [str(f.relative_to(self.temp_repo_cache)) for f in template_dir.rglob("*") if f.is_file()]
        )
        self.test_repo.index.commit("Add test-template")

        return template_dir

    def create_project_template_files(self) -> Path:
        """Create a local project template structure.

        Returns:
            Path to the created project template directory
        """
        # Create projects template structure
        template_dir = self.temp_repo_cache / "projects" / "test-project"
        template_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        (template_dir / "package.json").write_text('{"name": "test-project", "version": "1.0.0"}')
        (template_dir / "README.md").write_text("# Test Project\nThis is a test project template.\n")

        # Create subdirectory
        src_dir = template_dir / "src"
        src_dir.mkdir()
        (src_dir / "index.js").write_text('console.log("Hello from test project");')

        # Create metadata
        (template_dir / "metadata.toml").write_text("""
[template]
name = "test-project" 
description = "Test project template for unit testing"
type = "project"
version = "1.0.0"
""")

        # Add and commit files to Git repository
        self.test_repo.index.add(
            [str(f.relative_to(self.temp_repo_cache)) for f in template_dir.rglob("*") if f.is_file()]
        )
        self.test_repo.index.commit("Add test-project")

        return template_dir

    def invoke_cli_with_test_config(self, command_args: list[str], **kwargs):
        """Invoke CLI command with test configuration injected.

        Args:
            command_args: CLI command arguments
            **kwargs: Additional arguments for CliRunner.invoke

        Returns:
            Result from CLI invocation
        """
        # Inject test repository via CLI argument
        full_args = ["--repo", self.TEST_REPO_URL] + command_args

        # Mock the config loading and git operations to use our test setup
        with (
            patch("src.models.cli_config.CLIConfig.load_from_file") as mock_load,
            patch("src.models.cli_config.CLIConfig.get_repo_cache_dir") as mock_cache_dir,
            patch("src.lib.git_ops.GitOperations.sync_repository") as mock_sync,
        ):
            mock_load.return_value = self.test_config
            mock_cache_dir.return_value = self.temp_repo_cache
            mock_sync.return_value = True  # Always succeed sync

            from src.main import app

            return self.cli_runner.invoke(app, full_args, **kwargs)

    def assert_symlink_created(self, target_rel_path: str, expected_content: str = None):
        """Assert that a symlink was created correctly.

        Args:
            target_rel_path: Relative path from home directory (e.g., ".vimrc")
            expected_content: Expected content of the linked file (optional)
        """
        target_path = self.temp_home / target_rel_path

        # Check symlink exists
        assert target_path.exists(), f"Target file {target_path} does not exist"
        assert target_path.is_symlink(), f"Target file {target_path} is not a symlink"

        # Check content if provided
        if expected_content is not None:
            actual_content = target_path.read_text()
            assert expected_content in actual_content, f"Expected content not found in {target_path}"

    def assert_file_copied(self, target_rel_path: str, expected_content: str = None):
        """Assert that a file was copied correctly.

        Args:
            target_rel_path: Relative path from target directory
            expected_content: Expected content of the copied file (optional)
        """
        target_path = Path.cwd() / target_rel_path

        # Check file exists and is not a symlink
        assert target_path.exists(), f"Target file {target_path} does not exist"
        assert not target_path.is_symlink(), f"Target file {target_path} should not be a symlink"

        # Check content if provided
        if expected_content is not None:
            actual_content = target_path.read_text()
            assert expected_content in actual_content, f"Expected content not found in {target_path}"


@pytest.fixture
def isolated_env():
    """Pytest fixture providing isolated test environment."""
    test_env = TestWithIsolation()
    test_env.setup_method()
    yield test_env
    test_env.teardown_method()
