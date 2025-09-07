"""List command implementation for available templates."""

import logging

import typer
from rich.console import Console

from ..lib.render import render_json, render_text_templates
from ..lib.git_ops import GitOperations
from ..models.enums import TemplateKind
from ..lib.command_base import (
    get_command_context,
    sync_repo_if_needed,
    handle_command_error,
    ensure_repository_configured,
)

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
        # Unified command context and config
        context = get_command_context()
        ensure_repository_configured(context)

        git_ops = GitOperations()
        repo_cache_dir = context.config.get_repo_cache_dir()

        # Unified sync/clone logic
        sync_repo_if_needed(context, git_ops)

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

            if context.output_format == "json":
                render_json({"templates": []})
            else:
                console.print(f"[yellow]{message}[/yellow]")
            return

        # Output results
        if context.output_format == "json":
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

    except Exception as e:
        handle_command_error(e)
