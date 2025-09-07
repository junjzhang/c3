"""Install command implementation for dotfiles templates."""

import logging
from typing import Annotated

import typer
from rich.console import Console

from ..lib.git_ops import GitOperations
from ..lib.dotfiles import DotfilesManager
from ..models.cli_config import CLIConfig

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

        verbose = ctx.obj.get("verbose", False)
        output_format = ctx.obj.get("format", "text")

        # Setup managers
        git_ops = GitOperations()
        dotfiles_manager = DotfilesManager(user_home=config.user_home)

        # Get repository cache directory
        repo_cache_dir = config.get_repo_cache_dir()

        # Sync repository if needed
        if not repo_cache_dir.exists() or config.should_auto_sync():
            if verbose:
                console.print(f"Syncing repository from {config.default_repo_url}")

            if not repo_cache_dir.exists():
                # Clone repository
                success = git_ops.clone_repository(config.default_repo_url, repo_cache_dir, config.repo_branch)
                if not success:
                    console.print("[red]Error: Failed to clone repository[/red]")
                    raise typer.Exit(4)
            else:
                # Sync existing repository
                success = git_ops.sync_repository(repo_cache_dir, config.repo_branch)
                if not success:
                    console.print("[red]Error: Failed to sync repository[/red]")
                    raise typer.Exit(4)

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
        if output_format == "text":
            console.print(f"Installing dotfiles template: [bold]{template_name}[/bold]")
            if template.description:
                console.print(f"Description: {template.description}")

        success, links = dotfiles_manager.install_template(template, repo_cache_dir, force=force, dry_run=dry_run)

        if output_format == "text":
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
                            import subprocess

                            try:
                                result = subprocess.run(
                                    [str(script_path)],
                                    cwd=script_path.parent,
                                    check=True,
                                    capture_output=True,
                                    text=True,
                                )
                                console.print("✓ Executed install.sh successfully")
                                if verbose and result.stdout:
                                    console.print(result.stdout)
                            except subprocess.CalledProcessError as e:
                                console.print(f"[red]✗ Install script failed: {e}[/red]")
                                if e.stderr:
                                    console.print(f"[red]{e.stderr}[/red]")
                    else:
                        console.print("[yellow]DRY RUN: Would prompt to run install.sh[/yellow]")

        if success:
            if output_format == "text":
                console.print(f"[green]Template '{template_name}' installed successfully[/green]")
        else:
            if output_format == "text":
                console.print(f"[red]Template '{template_name}' installation failed[/red]")
            raise typer.Exit(2)

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during install: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
