"""Apply command implementation for project templates."""

import shutil
import logging
import subprocess
from typing import Annotated
from pathlib import Path

import typer
from rich.console import Console

from ..lib.git_ops import GitOperations
from ..lib.templates import TemplatesManager
from ..lib.command_base import (
    get_command_context,
    sync_repo_if_needed,
    handle_command_error,
    ensure_repository_configured,
)

logger = logging.getLogger(__name__)
console = Console()


def apply(
    template_name: Annotated[str, typer.Argument(help="Name of template to apply")],
    target: Annotated[
        Path | None, typer.Option("--target", help="Target directory (default: current directory)")
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
        # Get unified command context (replaces all the manual parsing above)
        context = get_command_context()
        ensure_repository_configured(context)

        # Determine target directory (Typer already parsed as Path)
        target_dir = target if target else Path.cwd()
        target_dir = target_dir.resolve()

        # Setup managers
        git_ops = GitOperations()
        templates_manager = TemplatesManager()

        # Get repository cache directory
        repo_cache_dir = context.config.get_repo_cache_dir()

        # Unified sync/clone logic
        sync_repo_if_needed(context, git_ops)

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
        if context.output_format == "text":
            console.print(f"Applying project template: [bold]{template_name}[/bold]")
            if template.description:
                console.print(f"Description: {template.description}")
            console.print(f"Target directory: {target_dir}")

        success, project_files = templates_manager.apply_template(
            template, repo_cache_dir, target_dir, force=force, dry_run=dry_run
        )

        if context.output_format == "text":
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
                                    shutil.copy2(script_path, temp_script)
                                    temp_script.chmod(0o755)

                                result = subprocess.run(
                                    [str(temp_script)], cwd=target_dir, check=True, capture_output=True, text=True
                                )
                                console.print("✓ Executed install.sh successfully")
                                if context.verbose and result.stdout:
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
            if context.output_format == "text":
                console.print(f"[green]Template '{template_name}' applied successfully[/green]")
        else:
            if context.output_format == "text":
                console.print(f"[red]Template '{template_name}' application failed[/red]")
            raise typer.Exit(2) from None

    except Exception as e:
        handle_command_error(e)
