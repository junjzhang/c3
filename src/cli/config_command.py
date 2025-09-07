"""Config command implementation for configuration management."""

import logging

import typer
from rich.console import Console

from ..lib.render import render_json
from ..lib.command_base import get_command_context, handle_command_error
from ..models.cli_config import CLIConfig

logger = logging.getLogger(__name__)
console = Console()

# Create config subcommand app
config_app = typer.Typer(name="config", help="Manage CLI configuration")


@config_app.command(name="list")
def list_config():
    """List all configuration settings."""
    try:
        context = get_command_context()
        config = context.config
        output_format = context.output_format

        if output_format == "json":
            config_dict = config.model_dump()
            render_json(config_dict)
        else:
            console.print("[bold]All Configuration Settings:[/bold]")
            console.print(f"repository.url: {config.default_repo_url or '[red]Not set[/red]'}")
            console.print(f"repository.branch: {config.repo_branch}")
            console.print(f"config.dir: {config.config_dir}")
            console.print(f"user.home: {config.user_home}")

    except Exception as e:
        handle_command_error(e)


@config_app.command(name="get")
def get_config(
    key: str = typer.Argument(..., help="Configuration key to get"),
):
    """Get configuration value by key."""
    try:
        context = get_command_context()
        config = context.config

        # Parse nested keys
        keys = key.split(".")

        if keys == ["repository", "url"]:
            value = config.default_repo_url or "Not set"
        elif keys == ["repository", "branch"]:
            value = config.repo_branch
        elif keys == ["config", "dir"]:
            value = str(config.config_dir)
        elif keys == ["user", "home"]:
            value = str(config.user_home)
        else:
            console.print(f"[red]Error: Unknown configuration key '{key}'[/red]")
            console.print("Valid keys: repository.url, repository.branch, config.dir, user.home")
            raise typer.Exit(1)

        console.print(f"{key}: {value}")

    except Exception as e:
        handle_command_error(e)


@config_app.command(name="show")
def show_config():
    """Show current configuration."""
    try:
        context = get_command_context()
        config = context.config
        output_format = context.output_format

        if output_format == "json":
            config_dict = config.model_dump()
            render_json(config_dict)
        else:
            console.print("[bold]Current Configuration:[/bold]")
            console.print(f"Repository URL: {config.default_repo_url or '[red]Not set[/red]'}")
            console.print(f"Repository Branch: {config.repo_branch}")

            if config.default_repo_url:
                console.print(f"Cache Directory: {config.get_repo_cache_dir()}")
                console.print(f"Auto Sync: {config.should_auto_sync()}")
            else:
                console.print("Cache Directory: [yellow]Not applicable (no repository configured)[/yellow]")
                console.print("Auto Sync: [yellow]Not applicable (no repository configured)[/yellow]")
            console.print(f"Config File: {config.config_dir / 'config.toml'}")

            if config.is_configured():
                console.print("\n[green]✓ Configuration is valid[/green]")
            else:
                console.print("\n[red]✗ Configuration is incomplete[/red]")
                console.print("Run 'c3cli config set repository.url <url>' to configure")

    except Exception as e:
        handle_command_error(e)


@config_app.command(name="set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key (e.g., repository.url, repository.branch)"),
    value: str = typer.Argument(..., help="Configuration value"),
):
    """Set configuration value."""
    try:
        context = get_command_context()
        config = context.config

        # Parse nested keys
        keys = key.split(".")

        if keys == ["repository", "url"]:
            config.default_repo_url = value
        elif keys == ["repository", "branch"]:
            config.repo_branch = value
        elif keys == ["cache", "dir"]:
            console.print("[red]Error: Cache directory cannot be set directly[/red]")
            console.print("It is computed from config directory and repository URL")
            raise typer.Exit(1)
        elif keys == ["auto", "sync"] or keys == ["auto_sync"]:
            console.print("[red]Error: Auto sync cannot be set directly[/red]")
            console.print("It is computed from repository configuration")
            raise typer.Exit(1)
        else:
            console.print(f"[red]Error: Unknown configuration key '{key}'[/red]")
            console.print("Valid keys: repository.url, repository.branch")
            raise typer.Exit(1)

        # Save configuration
        config.save_to_file()

        console.print(f"[green]✓ Set {key} = {value}[/green]")

        if config.is_configured():
            console.print("[green]Configuration is now complete[/green]")

    except Exception as e:
        handle_command_error(e)


@config_app.command(name="unset")
def unset_config(
    key: str = typer.Argument(..., help="Configuration key to unset"),
):
    """Unset configuration value."""
    try:
        context = get_command_context()
        config = context.config

        # Parse nested keys
        keys = key.split(".")

        if keys == ["repository", "url"]:
            config.default_repo_url = None
        elif keys == ["repository", "branch"]:
            config.repo_branch = "main"  # Reset to default
        else:
            console.print(f"[red]Error: Unknown configuration key '{key}'[/red]")
            console.print("Valid keys: repository.url, repository.branch")
            raise typer.Exit(1)

        # Save configuration
        config.save_to_file()

        console.print(f"[green]✓ Unset {key}[/green]")

    except Exception as e:
        handle_command_error(e)


@config_app.command(name="reset")
def reset_config(
    confirm: bool = typer.Option(False, "--confirm", help="Confirm reset without prompt"),
):
    """Reset configuration to defaults."""
    try:
        if not confirm:
            if not typer.confirm("Reset all configuration to defaults?"):
                console.print("Cancelled")
                return

        # Create new default config and save to current config file location
        context = get_command_context()
        config_path = context.config.config_dir / "config.toml"

        config = CLIConfig()
        config.save_to_file(config_path)

        console.print("[green]✓ Configuration reset to defaults[/green]")
        console.print("Run 'c3cli config set repository.url <url>' to configure")

    except Exception as e:
        handle_command_error(e)


# Main config command that uses the subcommand app
def config():
    """Manage CLI configuration."""
    config_app()
