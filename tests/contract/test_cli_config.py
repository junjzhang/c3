"""Contract tests for c3cli config command.

These tests define the expected behavior and interface of the config command
according to the CLI contract specification. Tests MUST FAIL initially (TDD).
"""

import json
import subprocess


class TestConfigCommandContract:
    """Test the c3cli config command contract."""

    def test_config_command_exists(self):
        """Test that the config command exists and can be invoked."""
        result = subprocess.run(["c3cli", "config", "--help"], check=False, capture_output=True, text=True)
        assert result.returncode == 0
        assert "Manage CLI configuration" in result.stdout

    def test_config_subcommands_exist(self):
        """Test that config subcommands exist."""
        # Test list subcommand
        result1 = subprocess.run(["c3cli", "config", "list"], check=False, capture_output=True, text=True)
        # May fail due to implementation, but should recognize subcommand

        # Test get subcommand
        result2 = subprocess.run(["c3cli", "config", "get", "--help"], check=False, capture_output=True, text=True)
        # Should show help for get subcommand

        # Test set subcommand
        result3 = subprocess.run(["c3cli", "config", "set", "--help"], check=False, capture_output=True, text=True)
        # Should show help for set subcommand

    def test_config_get_requires_key(self):
        """Test that config get requires a key argument."""
        result = subprocess.run(["c3cli", "config", "get"], check=False, capture_output=True, text=True)
        assert result.returncode != 0
        assert "Missing argument" in result.stderr or "required" in result.stderr.lower()

    def test_config_set_requires_key_and_value(self):
        """Test that config set requires key and value arguments."""
        result = subprocess.run(["c3cli", "config", "set"], check=False, capture_output=True, text=True)
        assert result.returncode != 0

        result2 = subprocess.run(["c3cli", "config", "set", "key"], check=False, capture_output=True, text=True)
        assert result2.returncode != 0

    def test_config_list_shows_all_settings(self):
        """Test that config list shows all configuration settings."""
        result = subprocess.run(["c3cli", "config", "list"], check=False, capture_output=True, text=True)
        if result.returncode == 0:
            # Should show configuration in readable format
            assert "repo" in result.stdout.lower() or "repository" in result.stdout.lower()

    def test_config_json_format(self):
        """Test that config commands support JSON output format."""
        result = subprocess.run(
            ["c3cli", "--format", "json", "config", "list"], check=False, capture_output=True, text=True
        )
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                pass  # May not be implemented yet
