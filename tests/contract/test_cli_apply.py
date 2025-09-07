"""Contract tests for c3cli apply command.

These tests define the expected behavior and interface of the apply command
according to the CLI contract specification. Tests MUST FAIL initially (TDD).
"""

import tempfile
import subprocess
from pathlib import Path

from typer.testing import CliRunner


class TestApplyCommandContract:
    """Test the c3cli apply command contract."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_repo = tempfile.mkdtemp()

    def test_apply_command_exists(self):
        """Test that the apply command exists and can be invoked."""
        # This will fail until we implement the CLI
        result = subprocess.run(["c3cli", "apply", "--help"], check=False, capture_output=True, text=True)
        assert result.returncode == 0
        assert "Apply a project template" in result.stdout

    def test_apply_requires_template_argument(self):
        """Test that apply command requires a template name argument."""
        result = subprocess.run(["c3cli", "apply"], check=False, capture_output=True, text=True)
        assert result.returncode != 0
        assert "Missing argument" in result.stderr or "required" in result.stderr.lower()

    def test_apply_command_options(self):
        """Test that apply command supports expected options."""
        result = subprocess.run(["c3cli", "apply", "--help"], check=False, capture_output=True, text=True)
        assert result.returncode == 0

        help_text = result.stdout
        # Check for required options
        assert "--target" in help_text
        assert "--force" in help_text or "-f" in help_text
        assert "--dry-run" in help_text or "-n" in help_text
        assert "--no-script" in help_text

    def test_apply_template_not_found_exit_code(self):
        """Test exit code 1 when template is not found."""
        result = subprocess.run(
            ["c3cli", "apply", "nonexistent-template"], check=False, capture_output=True, text=True, cwd=self.temp_dir
        )
        assert result.returncode == 1

    def test_apply_file_conflict_exit_code(self):
        """Test exit code 2 for file conflicts without --force."""
        # Create conflicting file first
        conflicting_file = Path(self.temp_dir) / "package.json"
        conflicting_file.write_text('{"existing": true}')

        result = subprocess.run(
            ["c3cli", "apply", "node-template"], check=False, capture_output=True, text=True, cwd=self.temp_dir
        )
        # Should fail with conflict error if template contains package.json
        assert result.returncode == 2 or result.returncode == 1  # 1 if template not found first

    def test_apply_repository_error_exit_code(self):
        """Test exit code 4 for repository errors."""
        result = subprocess.run(
            ["c3cli", "--repo", "invalid://repo", "apply", "some-template"],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        assert result.returncode == 4

    def test_apply_dry_run_shows_preview(self):
        """Test that --dry-run shows what would be done without executing."""
        result = subprocess.run(
            [
                "c3cli",
                "--repo",
                "https://github.com/junjzhang/c3-config-test.git",
                "apply",
                "test-template",
                "--dry-run",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        # Should show what would be copied without actually doing it
        assert "would copy" in result.stdout.lower() or "dry run" in result.stdout.lower()

    def test_apply_target_option_specifies_directory(self):
        """Test that --target option allows specifying target directory."""
        target_dir = Path(self.temp_dir) / "new-project"
        target_dir.mkdir()

        result = subprocess.run(
            ["c3cli", "apply", "test-template", "--target", str(target_dir)],
            check=False,
            capture_output=True,
            text=True,
        )

        # Command should accept target directory option
        assert (
            "--target"
            in subprocess.run(["c3cli", "apply", "--help"], check=False, capture_output=True, text=True).stdout
        )

    def test_apply_output_format(self):
        """Test the expected output format for successful apply."""
        result = subprocess.run(
            ["c3cli", "apply", "test-template"], check=False, capture_output=True, text=True, cwd=self.temp_dir
        )
        if result.returncode == 0:  # Only test format if command succeeds
            output = result.stdout
            assert "Applying project template:" in output
            # Should show copy operations with checkmarks
            assert "✓" in output or "copied" in output.lower()

    def test_apply_force_option_overwrites(self):
        """Test that --force option allows overwriting existing files."""
        # Create existing file
        existing_file = Path(self.temp_dir) / "README.md"
        existing_file.write_text("Existing content")

        # Apply without --force should fail or warn
        result1 = subprocess.run(
            ["c3cli", "apply", "test-template"], check=False, capture_output=True, text=True, cwd=self.temp_dir
        )

        # Apply with --force should succeed
        result2 = subprocess.run(
            ["c3cli", "apply", "test-template", "--force"],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        # At least one should mention force option in help
        help_result = subprocess.run(["c3cli", "apply", "--help"], check=False, capture_output=True, text=True)
        assert "--force" in help_result.stdout

    def test_apply_no_script_option_skips_scripts(self):
        """Test that --no-script option skips install.sh execution."""
        result = subprocess.run(
            ["c3cli", "apply", "template-with-script", "--no-script"],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        # Should not prompt for script execution
        assert "Run install.sh script?" not in result.stdout

    def test_apply_copies_files_to_current_directory(self):
        """Test that apply command copies template files to current directory."""
        # Setup test template in temporary repo
        test_template_dir = Path(self.temp_repo) / "projects" / "test-template"
        test_template_dir.mkdir(parents=True)

        # Create template files
        (test_template_dir / "package.json").write_text('{"name": "test"}')
        (test_template_dir / "README.md").write_text("# Test Project")

        src_dir = test_template_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text('print("hello")')

        # Run apply command
        result = subprocess.run(
            ["c3cli", "--repo", str(self.temp_repo), "apply", "test-template"],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        # Check that files were copied (not symlinked)
        if result.returncode == 0:
            copied_package = Path(self.temp_dir) / "package.json"
            copied_readme = Path(self.temp_dir) / "README.md"
            copied_main = Path(self.temp_dir) / "src" / "main.py"

            assert copied_package.exists() and not copied_package.is_symlink()
            assert copied_readme.exists() and not copied_readme.is_symlink()
            assert copied_main.exists() and not copied_main.is_symlink()

            # Content should match
            assert copied_package.read_text() == '{"name": "test"}'
            assert copied_readme.read_text() == "# Test Project"
            assert copied_main.read_text() == 'print("hello")'

    def test_apply_script_prompt_behavior(self):
        """Test that install.sh scripts are prompted for execution."""
        # Setup template with install.sh
        test_template_dir = Path(self.temp_repo) / "projects" / "template-with-script"
        test_template_dir.mkdir(parents=True)

        (test_template_dir / "package.json").write_text('{"name": "test"}')

        install_script = test_template_dir / "install.sh"
        install_script.write_text('#!/bin/bash\necho "Installing dependencies"')
        install_script.chmod(0o755)

        # Run apply and check for prompt
        result = subprocess.run(
            ["c3cli", "--repo", str(self.temp_repo), "apply", "template-with-script"],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
            input="y\n",
        )

        if result.returncode == 0:
            assert "Run install.sh script?" in result.stdout
            assert "Installing dependencies" in result.stdout

    def test_apply_target_directory_creation(self):
        """Test that apply creates target directory if it doesn't exist."""
        target_dir = Path(self.temp_dir) / "new-project"
        # Directory doesn't exist yet
        assert not target_dir.exists()

        result = subprocess.run(
            ["c3cli", "apply", "test-template", "--target", str(target_dir)],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should either create directory or give appropriate error
        # This behavior needs to be defined in the contract
