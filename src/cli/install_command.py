"""Install command implementation for dotfiles templates."""

import logging
import subprocess
from typing import Annotated

import typer
from rich.console import Console

from ..lib.git_ops import GitOperations
from ..lib.dotfiles import DotfilesManager
from ..lib.command_base import (
    get_command_context,
    handle_command_error,
    ensure_repository_configured,
)

logger = logging.getLogger(__name__)
console = Console()


def install(
    template_name: Annotated[str, typer.Argument(help="Name of template to install")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing files without prompt")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Show what would be done without executing")] = False,
    no_script: Annotated[bool, typer.Option("--no-script", help="Skip running install.sh if present")] = False,
):
    """Apply a dotfiles template using symbolic links.

    This command installs dotfiles templates by creating symbolic links
    from your home directory to files in the configuration repository.
    """
    try:
        # Get unified command context
        context = get_command_context()
        ensure_repository_configured(context)

        # Setup managers
        git_ops = GitOperations()
        dotfiles_manager = DotfilesManager(user_home=context.config.user_home)

        # Get repository cache directory
        repo_cache_dir = context.config.get_repo_cache_dir()

        # Sync repository if needed
        if not repo_cache_dir.exists() or context.config.should_auto_sync():
            if context.verbose:
                console.print(f"Syncing repository from {context.config.default_repo_url}")

            git_ops.ensure_repo(context.config.default_repo_url, context.config.repo_branch, repo_cache_dir)

        # Discover templates
        templates = git_ops.discover_templates(repo_cache_dir)
        dotfiles_templates = {t.name: t for t in templates if t.is_dotfiles_template()}

        # Find requested template
        if template_name not in dotfiles_templates:
            console.print(f"[red]Error: Template '{template_name}' not found[/red]")
            available = list(dotfiles_templates.keys())
            if available:
                console.print(f"Available dotfiles templates: {', '.join(available)}")
            raise typer.Exit(1)

        template = dotfiles_templates[template_name]

        # Install template
        if context.output_format == "text":
            console.print(f"Installing dotfiles template: [bold]{template_name}[/bold]")
            if template.description:
                console.print(f"Description: {template.description}")

        success, links = dotfiles_manager.install_template(template, repo_cache_dir, force=force, dry_run=dry_run)

        if context.output_format == "text":
            if dry_run:
                console.print(f"[yellow]DRY RUN: Would create {len(links)} symlinks[/yellow]")

            for link in links:
                status = "✓" if success else "✗"
                console.print(f"{status} {link.target} -> {link.source}")

            # Handle install script
            if template.has_install_script() and not no_script:
                script_path = template.get_install_script_path()
                if script_path and script_path.exists():
                    if not dry_run:
                        run_script = typer.confirm("Run install.sh script?")
                        if run_script:
                            try:
                                result = subprocess.run(
                                    [str(script_path)],
                                    cwd=script_path.parent,
                                    check=True,
                                    capture_output=True,
                                    text=True,
                                )
                                console.print("✓ Executed install.sh successfully")
                                if context.verbose and result.stdout:
                                    console.print(result.stdout)
                            except subprocess.CalledProcessError as e:
                                console.print(f"[red]✗ Install script failed: {e}[/red]")
                                if e.stderr:
                                    console.print(f"[red]{e.stderr}[/red]")
                    else:
                        console.print("[yellow]DRY RUN: Would prompt to run install.sh[/yellow]")

        if success:
            if context.output_format == "text":
                console.print(f"[green]Template '{template_name}' installed successfully[/green]")
        else:
            if context.output_format == "text":
                console.print(f"[red]Template '{template_name}' installation failed[/red]")
            raise typer.Exit(2)

    except Exception as e:
        handle_command_error(e)
