"""Apply command implementation for project templates."""

import logging
import subprocess
from typing import Annotated
from pathlib import Path

import typer
from rich.console import Console

from ..lib.git_ops import GitOperations
from ..lib.templates import TemplatesManager
from ..models.cli_config import CLIConfig

logger = logging.getLogger(__name__)
console = Console()


def apply(
    template_name: Annotated[str, typer.Argument(help="Name of template to apply")],
    target: Annotated[
        str | None, typer.Option("--target", help="Target directory (default: current directory)")
    ] = None,
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing files without prompt")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Show what would be done without executing")] = False,
    no_script: Annotated[bool, typer.Option("--no-script", help="Skip running install.sh if present")] = False,
):
    """Apply a project template by copying files to current directory.

    This command applies project templates by copying files from the template
    to the target directory for one-time project initialization.
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

        # Determine target directory
        target_dir = Path(target) if target else Path.cwd()
        target_dir = target_dir.resolve()

        # Setup managers
        git_ops = GitOperations()
        templates_manager = TemplatesManager()

        # Get repository cache directory
        repo_cache_dir = config.get_repo_cache_dir()

        # Sync repository if needed
        if not repo_cache_dir.exists() or config.should_auto_sync():
            if verbose:
                console.print(f"Syncing repository from {config.default_repo_url}")

            if not repo_cache_dir.exists():
                success = git_ops.clone_repository(config.default_repo_url, repo_cache_dir, config.repo_branch)
                if not success:
                    console.print("[red]Error: Failed to clone repository[/red]")
                    raise typer.Exit(4)
            else:
                success = git_ops.sync_repository(repo_cache_dir, config.repo_branch)
                if not success:
                    console.print("[red]Error: Failed to sync repository[/red]")
                    raise typer.Exit(4)

        # Discover templates
        templates = git_ops.discover_templates(repo_cache_dir)
        project_templates = {t.name: t for t in templates if t.is_project_template()}

        # Find requested template
        if template_name not in project_templates:
            console.print(f"[red]Error: Template '{template_name}' not found[/red]")
            available = list(project_templates.keys())
            if available:
                console.print(f"Available project templates: {', '.join(available)}")
            raise typer.Exit(1)

        template = project_templates[template_name]

        # Check for conflicts
        if not force:
            conflicts = templates_manager.check_file_conflicts(template, repo_cache_dir, target_dir)
            if conflicts:
                console.print(f"[yellow]Warning: {len(conflicts)} file conflicts detected:[/yellow]")
                for _source, target_path in conflicts:
                    console.print(f"  {target_path.name}")

                if not dry_run:
                    if not typer.confirm("Continue anyway?"):
                        console.print("Aborted")
                        raise typer.Exit(2)

        # Apply template
        if output_format == "text":
            console.print(f"Applying project template: [bold]{template_name}[/bold]")
            if template.description:
                console.print(f"Description: {template.description}")
            console.print(f"Target directory: {target_dir}")

        success, project_files = templates_manager.apply_template(
            template, repo_cache_dir, target_dir, force=force, dry_run=dry_run
        )

        if output_format == "text":
            if dry_run:
                console.print(f"[yellow]DRY RUN: Would copy {len(project_files)} files[/yellow]")

            for project_file in project_files:
                status = "✓" if success else "✗"
                relative_target = project_file.target.relative_to(target_dir)
                console.print(f"{status} {relative_target} copied")

            # Handle install script
            if template.has_install_script() and not no_script:
                script_path = template.get_install_script_path()
                if script_path and script_path.exists():
                    if not dry_run:
                        run_script = typer.confirm("Run install.sh script?")
                        if run_script:
                            try:
                                # Copy script to target directory temporarily for execution
                                temp_script = target_dir / "install.sh"
                                if not temp_script.exists():
                                    import shutil

                                    shutil.copy2(script_path, temp_script)
                                    temp_script.chmod(0o755)

                                result = subprocess.run(
                                    [str(temp_script)], cwd=target_dir, check=True, capture_output=True, text=True
                                )
                                console.print("✓ Executed install.sh successfully")
                                if verbose and result.stdout:
                                    console.print(result.stdout)

                                # Clean up temp script if we created it
                                if temp_script.exists() and temp_script != script_path:
                                    temp_script.unlink()

                            except subprocess.CalledProcessError as e:
                                console.print(f"[red]✗ Install script failed: {e}[/red]")
                                if e.stderr:
                                    console.print(f"[red]{e.stderr}[/red]")
                    else:
                        console.print("[yellow]DRY RUN: Would prompt to run install.sh[/yellow]")

        if success:
            if output_format == "text":
                console.print(f"[green]Template '{template_name}' applied successfully[/green]")
        else:
            if output_format == "text":
                console.print(f"[red]Template '{template_name}' application failed[/red]")
            raise typer.Exit(2) from None

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during apply: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
