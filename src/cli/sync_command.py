"""Sync command implementation for repository synchronization."""

import logging

import typer
from rich.console import Console

from ..lib.git_ops import GitOperations
from ..models.cli_config import CLIConfig

logger = logging.getLogger(__name__)
console = Console()


def sync(
    branch: str = typer.Option(None, "--branch", help="Branch to sync (overrides config)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force sync, overwriting local changes"),
):
    """Synchronize with remote configuration repository.

    Updates the local repository cache by pulling the latest changes
    from the configured remote repository.
    """
    try:
        # Get context and load configuration
        import click

        ctx = click.get_current_context()
        config = CLIConfig.load_from_file(ctx.obj.get("config_path"))

        if ctx.obj.get("repo_override"):
            try:
                config.default_repo_url = ctx.obj["repo_override"]
            except Exception as e:
                console.print(f"[red]Error: Invalid repository URL: {e}[/red]")
                raise typer.Exit(4)

        if not config.is_configured():
            console.print("[red]Error: No repository configured. Use 'c3cli config set repository.url <url>'[/red]")
            raise typer.Exit(1)

        # Use branch parameter if provided, otherwise use config default
        sync_branch = branch if branch is not None else config.repo_branch

        verbose = ctx.obj.get("verbose", False)
        output_format = ctx.obj.get("format", "text")

        # Setup Git operations
        git_ops = GitOperations()
        repo_cache_dir = config.get_repo_cache_dir()

        if output_format == "text":
            console.print(f"Syncing with repository: [bold]{config.default_repo_url}[/bold]")
            console.print(f"Branch: {sync_branch}")
            console.print(f"Cache directory: {repo_cache_dir}")

        # Sync repository
        if not repo_cache_dir.exists():
            # Clone repository
            success = git_ops.clone_repository(config.default_repo_url, repo_cache_dir, sync_branch)
            if success:
                if output_format == "text":
                    console.print("[green]✓ Repository cloned successfully[/green]")
            else:
                console.print("[red]Error: Failed to clone repository[/red]")
                raise typer.Exit(4)
        else:
            # Sync existing repository
            success = git_ops.sync_repository(repo_cache_dir, sync_branch, force=force)
            if success:
                if output_format == "text":
                    console.print("[green]✓ Repository synchronized successfully[/green]")
            else:
                console.print("[red]Error: Failed to sync repository[/red]")
                raise typer.Exit(4)

        # Show template count if verbose
        if verbose:
            templates = git_ops.discover_templates(repo_cache_dir)
            dotfiles_count = len([t for t in templates if t.is_dotfiles_template()])
            projects_count = len([t for t in templates if t.is_project_template()])

            if output_format == "text":
                console.print(
                    f"Found {len(templates)} templates ({dotfiles_count} dotfiles, {projects_count} projects)"
                )

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during sync: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
