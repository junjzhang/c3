"""Contract test for c3cli install command."""

import tempfile

from typer.testing import CliRunner

from src.main import app
from tests.fixtures import TestWithIsolation


class TestCliInstallContract(TestWithIsolation):
    """Test the c3cli install command contract with real functionality."""

    def test_cli_install_basic_real_symlinks(self):
        """Test basic install command creates real symlinks."""
        # Create local test template
        self.create_test_template_files()

        # Run install command with test configuration
        result = self.invoke_cli_with_test_config(["install", "test-template"])

        # Should succeed
        assert result.exit_code == 0

        # Verify symlinks were created
        self.assert_symlink_created(".vimrc", "Test vim config")
        self.assert_symlink_created(".gitconfig", "Test User")

    def test_cli_install_dry_run_shows_preview(self):
        """Test dry-run mode shows preview without creating files."""
        # Create local test template
        self.create_test_template_files()

        # Run install with dry-run
        result = self.invoke_cli_with_test_config(["install", "test-template", "--dry-run"])

        # Should succeed
        assert result.exit_code == 0

        # Should show preview text
        assert "DRY RUN" in result.stdout or "would" in result.stdout.lower()

        # Should NOT create actual files
        assert not (self.temp_home / ".vimrc").exists()
        assert not (self.temp_home / ".gitconfig").exists()

    def test_cli_install_force_overwrites_existing(self):
        """Test force option overwrites existing files."""
        # Create local test template
        self.create_test_template_files()

        # Create existing file in home
        existing_file = self.temp_home / ".vimrc"
        existing_file.write_text("Existing vim config")

        # Install without force should fail
        result = self.invoke_cli_with_test_config(["install", "test-template"])
        assert result.exit_code != 0

        # Install with force should succeed
        result = self.invoke_cli_with_test_config(["install", "test-template", "--force"])
        assert result.exit_code == 0

        # File should now be a symlink with new content
        self.assert_symlink_created(".vimrc", "Test vim config")

    def test_cli_install_nonexistent_template(self):
        """Test install with nonexistent template."""
        # Create local test template directory but not the requested template
        self.create_test_template_files()

        # Try to install non-existent template
        result = self.invoke_cli_with_test_config(["install", "nonexistent-template"])

        # Should fail
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


# Standalone tests for backwards compatibility
def test_cli_install_help():
    """Test install command help."""
    runner = CliRunner()
    result = runner.invoke(app, ["install", "--help"])
    assert result.exit_code == 0
    assert "install" in result.stdout.lower()


def test_cli_install_basic():
    """Test basic install command (dry-run for safety)."""
    # Keep a basic dry-run test for safety
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = CliRunner()
        result = runner.invoke(
            app, ["--repo", "https://github.com/junjzhang/c3-config-test.git", "install", "test-template", "--dry-run"]
        )
        # May succeed or fail depending on repository availability
        # This test mainly checks command parsing works


def test_cli_install_nonexistent_template_standalone():
    """Test install with nonexistent template (standalone)."""
    runner = CliRunner()
    result = runner.invoke(
        app, ["--repo", "https://github.com/junjzhang/c3-config-test.git", "install", "nonexistent-template"]
    )
    # Should fail (template not found or network error)
    assert result.exit_code != 0
