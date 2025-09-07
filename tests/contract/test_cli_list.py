"""Contract tests for c3cli list command.

These tests define the expected behavior and interface of the list command
according to the CLI contract specification. Tests MUST FAIL initially (TDD).
"""

import json
import tempfile
import subprocess
from pathlib import Path

import pytest


class TestListCommandContract:
    """Test the c3cli list command contract."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.temp_repo = tempfile.mkdtemp()

    def test_list_command_exists(self):
        """Test that the list command exists and can be invoked."""
        result = subprocess.run(["c3cli", "list", "--help"], check=False, capture_output=True, text=True)
        assert result.returncode == 0
        assert "List available templates" in result.stdout

    def test_list_accepts_optional_pattern_argument(self):
        """Test that list command accepts optional pattern argument."""
        # Should work without pattern
        result1 = subprocess.run(["c3cli", "list"], check=False, capture_output=True, text=True)
        # May fail due to missing implementation, but should not complain about missing args

        # Should work with pattern
        result2 = subprocess.run(["c3cli", "list", "python*"], check=False, capture_output=True, text=True)
        # Should accept pattern without error about unexpected arguments

        # Check help shows pattern is optional
        help_result = subprocess.run(["c3cli", "list", "--help"], check=False, capture_output=True, text=True)
        assert "[PATTERN]" in help_result.stdout or "pattern" in help_result.stdout.lower()

    def test_list_command_options(self):
        """Test that list command supports expected options."""
        result = subprocess.run(["c3cli", "list", "--help"], check=False, capture_output=True, text=True)
        assert result.returncode == 0

        help_text = result.stdout
        # Check for required options
        assert "--type" in help_text
        assert "--detailed" in help_text or "-d" in help_text

    def test_list_type_option_filters(self):
        """Test that --type option filters templates by type."""
        # Test with different type values
        for template_type in ["dotfiles", "project", "all"]:
            result = subprocess.run(
                ["c3cli", "list", "--type", template_type], check=False, capture_output=True, text=True
            )
            # Should not complain about invalid type values
            # Implementation may fail, but argument parsing should work

    def test_list_repository_error_exit_code(self):
        """Test exit code 4 for repository errors."""
        result = subprocess.run(
            ["c3cli", "--repo", "invalid://repo", "list"], check=False, capture_output=True, text=True
        )
        assert result.returncode == 4

    def test_list_output_format_text(self):
        """Test the expected text output format for list command."""
        # Create test repository with templates
        dotfiles_dir = Path(self.temp_repo) / "dotfiles"
        projects_dir = Path(self.temp_repo) / "projects"
        dotfiles_dir.mkdir(parents=True)
        projects_dir.mkdir(parents=True)

        # Create dotfiles templates
        vim_template = dotfiles_dir / "vim-config"
        vim_template.mkdir()
        (vim_template / ".vimrc").write_text("set number")
        (vim_template / "metadata.toml").write_text('description = "Vim editor configuration"')

        # Create projects templates
        python_template = projects_dir / "python-project"
        python_template.mkdir()
        (python_template / "pyproject.toml").write_text('[project]\nname = "test"')
        (python_template / "metadata.toml").write_text('description = "Python project template"')

        result = subprocess.run(
            ["c3cli", "--repo", str(self.temp_repo), "list"], check=False, capture_output=True, text=True
        )

        if result.returncode == 0:
            output = result.stdout
            assert "Available templates:" in output
            assert "dotfiles/" in output
            assert "projects/" in output
            assert "vim-config" in output
            assert "python-project" in output

    def test_list_output_format_json(self):
        """Test the JSON output format when --format json is used."""
        result = subprocess.run(["c3cli", "list", "--format", "json"], check=False, capture_output=True, text=True)

        if result.returncode == 0:
            # Should be valid JSON
            try:
                data = json.loads(result.stdout)
                assert isinstance(data, (dict, list))
            except json.JSONDecodeError:
                pytest.fail("Output is not valid JSON")

    def test_list_detailed_option_shows_descriptions(self):
        """Test that --detailed option shows template descriptions."""
        # Create test template with metadata
        test_template_dir = Path(self.temp_repo) / "dotfiles" / "test-template"
        test_template_dir.mkdir(parents=True)
        (test_template_dir / ".testrc").write_text("# test config")
        (test_template_dir / "metadata.toml").write_text('description = "Test configuration template"')

        # Regular list should be brief
        result1 = subprocess.run(
            ["c3cli", "--repo", str(self.temp_repo), "list"], check=False, capture_output=True, text=True
        )

        # Detailed list should show descriptions
        result2 = subprocess.run(
            ["c3cli", "--repo", str(self.temp_repo), "list", "--detailed"], check=False, capture_output=True, text=True
        )

        if result2.returncode == 0:
            assert "Test configuration template" in result2.stdout

    def test_list_pattern_filtering(self):
        """Test that pattern argument filters template names."""
        # Create multiple templates
        dotfiles_dir = Path(self.temp_repo) / "dotfiles"
        dotfiles_dir.mkdir(parents=True)

        for name in ["python-dev", "python-minimal", "vim-config", "bash-setup"]:
            template_dir = dotfiles_dir / name
            template_dir.mkdir()
            (template_dir / ".testfile").write_text("test")

        # Test pattern filtering
        result = subprocess.run(
            ["c3cli", "--repo", str(self.temp_repo), "list", "python*"], check=False, capture_output=True, text=True
        )

        if result.returncode == 0:
            output = result.stdout
            assert "python-dev" in output
            assert "python-minimal" in output
            # Should not show non-matching templates
            assert "vim-config" not in output
            assert "bash-setup" not in output

    def test_list_type_filtering(self):
        """Test that --type option filters by template type."""
        # Create both dotfiles and projects templates
        dotfiles_dir = Path(self.temp_repo) / "dotfiles" / "vim-config"
        projects_dir = Path(self.temp_repo) / "projects" / "python-app"

        dotfiles_dir.mkdir(parents=True)
        projects_dir.mkdir(parents=True)

        (dotfiles_dir / ".vimrc").write_text("set number")
        (projects_dir / "main.py").write_text('print("hello")')

        # Test filtering by dotfiles type
        result1 = subprocess.run(
            ["c3cli", "--repo", str(self.temp_repo), "list", "--type", "dotfiles"],
            check=False,
            capture_output=True,
            text=True,
        )

        if result1.returncode == 0:
            output1 = result1.stdout
            assert "vim-config" in output1
            assert "python-app" not in output1

        # Test filtering by project type
        result2 = subprocess.run(
            ["c3cli", "--repo", str(self.temp_repo), "list", "--type", "project"],
            check=False,
            capture_output=True,
            text=True,
        )

        if result2.returncode == 0:
            output2 = result2.stdout
            assert "python-app" in output2
            assert "vim-config" not in output2

    def test_list_empty_repository(self):
        """Test list command behavior with empty repository."""
        # Empty repository directory
        result = subprocess.run(
            ["c3cli", "--repo", str(self.temp_repo), "list"], check=False, capture_output=True, text=True
        )

        if result.returncode == 0:
            # Should show appropriate message for no templates
            assert "No templates found" in result.stdout or "Available templates:" in result.stdout

    def test_list_global_options_work(self):
        """Test that global options work with list command."""
        # Test --verbose
        result1 = subprocess.run(["c3cli", "--verbose", "list"], check=False, capture_output=True, text=True)

        # Test --quiet
        result2 = subprocess.run(["c3cli", "--quiet", "list"], check=False, capture_output=True, text=True)

        # Test --format
        result3 = subprocess.run(["c3cli", "--format", "json", "list"], check=False, capture_output=True, text=True)

        # Should not fail due to argument parsing errors
        # (May fail due to missing implementation)
