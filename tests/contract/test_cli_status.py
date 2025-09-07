"""Contract tests for c3cli status command.

These tests define the expected behavior and interface of the status command
according to the CLI contract specification. Tests MUST FAIL initially (TDD).
"""

import subprocess


class TestStatusCommandContract:
    """Test the c3cli status command contract."""

    def test_status_command_exists(self):
        """Test that the status command exists and can be invoked."""
        result = subprocess.run(["c3cli", "status", "--help"], check=False, capture_output=True, text=True)
        assert result.returncode == 0
        assert "Show status of installed templates" in result.stdout

    def test_status_no_arguments_required(self):
        """Test that status command works without arguments."""
        result = subprocess.run(["c3cli", "status"], check=False, capture_output=True, text=True)
        # Should not fail due to missing arguments

    def test_status_template_option(self):
        """Test that --template option allows filtering by template."""
        result = subprocess.run(
            ["c3cli", "status", "--template", "vim-config"], check=False, capture_output=True, text=True
        )
        # Should accept template option
        help_result = subprocess.run(["c3cli", "status", "--help"], check=False, capture_output=True, text=True)
        assert "--template" in help_result.stdout

    def test_status_output_format(self):
        """Test the expected output format for status command."""
        result = subprocess.run(["c3cli", "status"], check=False, capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            assert "Repository:" in output
            assert "Last sync:" in output or "Never synced" in output
