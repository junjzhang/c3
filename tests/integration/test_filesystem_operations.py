"""Integration tests for filesystem operations (symlinks and file copying).

These tests verify filesystem operations work correctly with real files.
Tests MUST FAIL initially (TDD).
"""

import os
import shutil
import tempfile
from pathlib import Path


class TestFilesystemOperationsIntegration:
    """Test filesystem operations integration."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.temp_source = tempfile.mkdtemp()
        self.temp_target = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_source, ignore_errors=True)
        shutil.rmtree(self.temp_target, ignore_errors=True)

    def test_can_create_symlinks(self):
        """Test that we can create symbolic links correctly."""
        from src.lib.dotfiles import DotfilesManager

        dotfiles_manager = DotfilesManager()

        # Create source file
        source_file = Path(self.temp_source) / ".testrc"
        source_file.write_text("# Test configuration")

        # Create symlink
        target_file = Path(self.temp_target) / ".testrc"
        success = dotfiles_manager.create_symlink(source_file, target_file)

        assert success
        assert target_file.is_symlink()
        assert target_file.resolve() == source_file.resolve()
        assert target_file.read_text() == "# Test configuration"

    def test_can_create_directory_symlinks(self):
        """Test that we can create symbolic links to directories."""
        from src.lib.dotfiles import DotfilesManager

        dotfiles_manager = DotfilesManager()

        # Create source directory with files
        source_dir = Path(self.temp_source) / ".config"
        source_dir.mkdir()
        (source_dir / "settings.json").write_text('{"theme": "dark"}')

        # Create symlink to directory
        target_dir = Path(self.temp_target) / ".config"
        success = dotfiles_manager.create_symlink(source_dir, target_dir)

        assert success
        assert target_dir.is_symlink()
        assert target_dir.resolve() == source_dir.resolve()

        # Verify file access through symlink
        settings_file = target_dir / "settings.json"
        assert settings_file.read_text() == '{"theme": "dark"}'

    def test_can_copy_files(self):
        """Test that we can copy files correctly."""
        from src.lib.templates import TemplatesManager

        templates_manager = TemplatesManager()

        # Create source files
        source_dir = Path(self.temp_source) / "template"
        source_dir.mkdir()
        (source_dir / "package.json").write_text('{"name": "test"}')
        (source_dir / "README.md").write_text("# Test Project")

        # Create subdirectory
        src_subdir = source_dir / "src"
        src_subdir.mkdir()
        (src_subdir / "main.py").write_text('print("hello")')

        # Copy template
        success = templates_manager.copy_template(source_dir, Path(self.temp_target))

        assert success

        # Verify files were copied (not symlinked)
        copied_package = Path(self.temp_target) / "package.json"
        copied_readme = Path(self.temp_target) / "README.md"
        copied_main = Path(self.temp_target) / "src" / "main.py"

        assert copied_package.exists() and not copied_package.is_symlink()
        assert copied_readme.exists() and not copied_readme.is_symlink()
        assert copied_main.exists() and not copied_main.is_symlink()

        # Verify content
        assert copied_package.read_text() == '{"name": "test"}'
        assert copied_readme.read_text() == "# Test Project"
        assert copied_main.read_text() == 'print("hello")'

    def test_handles_file_conflicts(self):
        """Test handling of file conflicts during operations."""
        from src.lib.dotfiles import DotfilesManager

        dotfiles_manager = DotfilesManager()

        # Create source file
        source_file = Path(self.temp_source) / ".bashrc"
        source_file.write_text("export PATH=$PATH:/usr/local/bin")

        # Create existing target file
        target_file = Path(self.temp_target) / ".bashrc"
        target_file.write_text("# Existing bashrc")

        # Try to create symlink without force - should fail
        success = dotfiles_manager.create_symlink(source_file, target_file, force=False)
        assert not success

        # Try with force - should succeed
        success = dotfiles_manager.create_symlink(source_file, target_file, force=True)
        assert success
        assert target_file.is_symlink()

    def test_handles_permission_errors(self):
        """Test handling of permission errors."""
        from src.lib.dotfiles import DotfilesManager

        dotfiles_manager = DotfilesManager()

        # Create source file
        source_file = Path(self.temp_source) / ".testrc"
        source_file.write_text("test content")

        # Create read-only target directory
        readonly_dir = Path(self.temp_target) / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        try:
            target_file = readonly_dir / ".testrc"
            success = dotfiles_manager.create_symlink(source_file, target_file)
            assert not success
        finally:
            # Cleanup: restore permissions
            readonly_dir.chmod(0o755)

    def test_preserves_file_permissions(self):
        """Test that file permissions are preserved during copying."""
        from src.lib.templates import TemplatesManager

        templates_manager = TemplatesManager()

        # Create executable script
        source_dir = Path(self.temp_source) / "template"
        source_dir.mkdir()
        script_file = source_dir / "install.sh"
        script_file.write_text('#!/bin/bash\necho "Installing"')
        script_file.chmod(0o755)  # Make executable

        # Copy template
        success = templates_manager.copy_template(source_dir, Path(self.temp_target))
        assert success

        # Verify permissions preserved
        copied_script = Path(self.temp_target) / "install.sh"
        assert copied_script.exists()
        assert os.access(copied_script, os.X_OK)  # Should be executable

    def test_handles_broken_symlinks(self):
        """Test handling of broken symbolic links."""
        from src.lib.dotfiles import DotfilesManager

        dotfiles_manager = DotfilesManager()

        # Create symlink to non-existent file
        source_file = Path(self.temp_source) / ".missing"
        target_file = Path(self.temp_target) / ".testlink"

        # This should fail gracefully
        success = dotfiles_manager.create_symlink(source_file, target_file)
        assert not success

    def test_can_list_symlinks_status(self):
        """Test that we can check the status of created symlinks."""
        from src.lib.dotfiles import DotfilesManager

        dotfiles_manager = DotfilesManager()

        # Create some symlinks
        source_file1 = Path(self.temp_source) / ".vimrc"
        source_file1.write_text("set number")
        target_file1 = Path(self.temp_target) / ".vimrc"

        source_file2 = Path(self.temp_source) / ".bashrc"
        source_file2.write_text('export PS1="$ "')
        target_file2 = Path(self.temp_target) / ".bashrc"

        dotfiles_manager.create_symlink(source_file1, target_file1)
        dotfiles_manager.create_symlink(source_file2, target_file2)

        # Check status
        status = dotfiles_manager.check_symlinks_status(Path(self.temp_target))

        assert len(status) >= 2
        assert any(s["target"] == str(target_file1) for s in status)
        assert any(s["target"] == str(target_file2) for s in status)
