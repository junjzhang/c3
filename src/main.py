"""Main CLI application for Claude Code Configuration Manager."""

import logging
from pathlib import Path

import click
import typer
from rich.logging import RichHandler

from . import __version__
from .models.enums import OutputFormat
from .models.cli_config import CLIConfig

# Global state
app = typer.Typer(
    name="c3cli",
    help="Claude Code Configuration Manager CLI",
    add_completion=True,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

_FORMAT_OPTION = typer.Option(OutputFormat.TEXT, "--format", help="Output format")


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Setup logging configuration."""
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format="%(name)s: %(message)s", handlers=[RichHandler(rich_tracebacks=True)])


def load_config(config_path: Path | None = None) -> CLIConfig:
    """Load CLI configuration."""
    try:
        return CLIConfig.load_from_file(config_path)
    except Exception as e:
        typer.echo(f"Error loading configuration: {e}", err=True)
        raise typer.Exit(1)


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
    config: str | None = typer.Option(None, "--config", help="Path to config file"),
    repo: str | None = typer.Option(None, "--repo", help="Config repository URL (overrides config file)"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-error output"),
    format_type: OutputFormat = _FORMAT_OPTION,
):
    """Claude Code Configuration Manager CLI.

    Manage dotfiles and project templates from Git repositories.
    """
    if version:
        typer.echo(f"c3cli version {__version__}")
        raise typer.Exit()

    # Setup logging
    setup_logging(verbose, quiet)

    # Create unified command context
    ctx = click.get_current_context()
    ctx.ensure_object(dict)
    from .lib.command_base import CommandContext, handle_command_error

    try:
        ctx.obj = CommandContext.from_cli_args(
            config_path=config,
            repo_override=repo,
            verbose=verbose,
            quiet=quiet,
            format_type=format_type.value,
        )
    except Exception as e:
        # Ensure repository/config errors return consistent exit codes during callback
        handle_command_error(e)


# Import and register commands
from .cli.list_command import list_templates
from .cli.sync_command import sync
from .cli.apply_command import apply
from .cli.config_command import config_app
from .cli.status_command import status
from .cli.install_command import install

app.command(name="install")(install)
app.command(name="apply")(apply)
app.command(name="list")(list_templates)
app.command(name="sync")(sync)
app.command(name="status")(status)
app.add_typer(config_app, name="config")


def cli():
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    cli()
