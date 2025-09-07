"""List command implementation for available templates."""

import json
import logging

import typer
from rich import print
from rich.table import Table
from rich.console import Console

from ..lib.git_ops import GitOperations
from ..models.cli_config import CLIConfig

logger = logging.getLogger(__name__)
console = Console()


def list_templates(
    pattern: str | None = typer.Argument(None, help="Filter templates by pattern (glob-style)"),
    template_type: str = typer.Option("all", "--type", help="Filter by type: dotfiles, projects, all"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information including descriptions"),
):
    """List available templates from the configuration repository.

    Shows all available templates with optional filtering by pattern and type.
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

        # Setup Git operations
        git_ops = GitOperations()
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

        # Filter by type
        if template_type.lower() == "dotfiles":
            templates = [t for t in templates if t.is_dotfiles_template()]
        elif template_type.lower() == "projects":
            templates = [t for t in templates if t.is_project_template()]
        # "all" includes everything

        # Filter by pattern
        if pattern:
            import fnmatch

            templates = [t for t in templates if fnmatch.fnmatch(t.name, pattern)]

        if not templates:
            message = "No templates found"
            if pattern:
                message += f" matching pattern '{pattern}'"
            if template_type != "all":
                message += f" of type '{template_type}'"

            if output_format == "json":
                print(json.dumps({"templates": []}))
            else:
                console.print(f"[yellow]{message}[/yellow]")
            return

        # Output results
        if output_format == "json":
            template_data = []
            for template in templates:
                template_info = {
                    "name": template.name,
                    "type": template.type,
                    "description": template.description,
                    "files_count": len(template.files),
                    "has_install_script": template.has_install_script(),
                }
                if detailed:
                    template_info.update(
                        {
                            "files": template.files,
                            "metadata": template.metadata,
                        }
                    )
                template_data.append(template_info)

            print(json.dumps({"templates": template_data}, indent=2))

        else:
            # Text output
            console.print("[bold]Available templates:[/bold]")

            # Group by type for better display
            dotfiles = [t for t in templates if t.is_dotfiles_template()]
            projects = [t for t in templates if t.is_project_template()]

            if dotfiles:
                console.print("\n[bold cyan]dotfiles/[/bold cyan]")
                if detailed:
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Name")
                    table.add_column("Description")
                    table.add_column("Files")
                    table.add_column("Script")

                    for template in sorted(dotfiles, key=lambda t: t.name):
                        script_indicator = "✓" if template.has_install_script() else ""
                        table.add_row(template.name, template.description, str(len(template.files)), script_indicator)
                    console.print(table)
                else:
                    for template in sorted(dotfiles, key=lambda t: t.name):
                        script_indicator = " (with install.sh)" if template.has_install_script() else ""
                        console.print(f"  [green]{template.name}[/green] - {template.description}{script_indicator}")

            if projects:
                console.print("\n[bold cyan]projects/[/bold cyan]")
                if detailed:
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Name")
                    table.add_column("Description")
                    table.add_column("Files")
                    table.add_column("Script")

                    for template in sorted(projects, key=lambda t: t.name):
                        script_indicator = "✓" if template.has_install_script() else ""
                        table.add_row(template.name, template.description, str(len(template.files)), script_indicator)
                    console.print(table)
                else:
                    for template in sorted(projects, key=lambda t: t.name):
                        script_indicator = " (with install.sh)" if template.has_install_script() else ""
                        console.print(f"  [green]{template.name}[/green] - {template.description}{script_indicator}")

            console.print(f"\nTotal: {len(templates)} template{'s' if len(templates) != 1 else ''}")

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during list: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
