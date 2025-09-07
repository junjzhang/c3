"""List command implementation for available templates."""

import logging

import click
import typer
from rich.console import Console

from ..lib.render import render_json, render_text_templates
from ..lib.git_ops import GitOperations
from ..models.enums import TemplateKind
from ..models.cli_config import CLIConfig

logger = logging.getLogger(__name__)
console = Console()


_PATTERN_ARG = typer.Argument(None, help="Filter templates by pattern (glob-style)")
_TYPE_OPTION = typer.Option(TemplateKind.ALL, "--type", help="Filter by type")
_DETAILED_OPTION = typer.Option(False, "--detailed", "-d", help="Show detailed information including descriptions")


def list_templates(
    pattern: str | None = _PATTERN_ARG,
    template_type: TemplateKind = _TYPE_OPTION,
    detailed: bool = _DETAILED_OPTION,
):
    """List available templates from the configuration repository.

    Shows all available templates with optional filtering by pattern and type.
    """
    try:
        # Get context and load configuration
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

            git_ops.ensure_repo(config.default_repo_url, config.repo_branch, repo_cache_dir)

        # Discover templates
        templates = git_ops.discover_templates(repo_cache_dir)

        # Filter by type
        if template_type == TemplateKind.DOTFILES:
            templates = [t for t in templates if t.is_dotfiles_template()]
        elif template_type == TemplateKind.PROJECTS:
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
            if template_type != TemplateKind.ALL:
                message += f" of type '{template_type.value}'"

            if output_format == "json":
                render_json({"templates": []})
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

            render_json({"templates": template_data})

        else:
            render_text_templates(templates, detailed=detailed)

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during list: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
