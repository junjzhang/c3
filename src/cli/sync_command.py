"""Sync command implementation for repository synchronization."""

import logging

import typer
from rich.console import Console

from ..lib.git_ops import GitOperations
from ..lib.command_base import (
    RepositoryError,
    get_command_context,
    handle_command_error,
    ensure_repository_configured,
)

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
        # Get unified command context
        context = get_command_context()
        ensure_repository_configured(context)

        # Use branch parameter if provided, otherwise use config default
        sync_branch = branch if branch is not None else context.config.repo_branch

        # Setup Git operations
        git_ops = GitOperations()
        repo_cache_dir = context.config.get_repo_cache_dir()

        if context.output_format == "text":
            console.print(f"Syncing with repository: [bold]{context.config.default_repo_url}[/bold]")
            console.print(f"Branch: {sync_branch}")
            console.print(f"Cache directory: {repo_cache_dir}")

        # Sync repository
        if not repo_cache_dir.exists():
            # Clone repository
            success = git_ops.clone_repository(context.config.default_repo_url, repo_cache_dir, sync_branch)
            if success:
                if context.output_format == "text":
                    console.print("[green]✓ Repository cloned successfully[/green]")
            else:
                raise RepositoryError("Failed to clone repository")
        else:
            # Sync existing repository
            success = git_ops.sync_repository(repo_cache_dir, sync_branch, force=force)
            if success:
                if context.output_format == "text":
                    console.print("[green]✓ Repository synchronized successfully[/green]")
            else:
                raise RepositoryError("Failed to sync repository")

        # Show template count if verbose
        if context.verbose:
            templates = git_ops.discover_templates(repo_cache_dir)
            dotfiles_count = len([t for t in templates if t.is_dotfiles_template()])
            projects_count = len([t for t in templates if t.is_project_template()])

            if context.output_format == "text":
                console.print(
                    f"Found {len(templates)} templates ({dotfiles_count} dotfiles, {projects_count} projects)"
                )

    except Exception as e:
        handle_command_error(e)
