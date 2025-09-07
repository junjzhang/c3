"""Status command implementation for installation status."""

import logging

import typer
from rich.console import Console

from ..lib.render import render_json, render_text_status
from ..lib.git_ops import GitOperations
from ..lib.dotfiles import DotfilesManager
from ..lib.command_base import (
    get_command_context,
    handle_command_error,
    ensure_repository_configured,
)

logger = logging.getLogger(__name__)
console = Console()


def status(
    template: str = typer.Option(None, "--template", help="Filter status by specific template"),
):
    """Show status of installed templates and symlinks.

    Displays information about currently installed dotfiles templates,
    their symlink status, and any broken or missing links.
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

        if not repo_cache_dir.exists():
            console.print("[yellow]Warning: Repository cache not found. Run 'c3cli sync' first.[/yellow]")
            raise typer.Exit(1)

        # Discover templates
        templates = git_ops.discover_templates(repo_cache_dir)
        dotfiles_templates = [t for t in templates if t.is_dotfiles_template()]

        # Filter by template name if specified
        if template:
            dotfiles_templates = [t for t in dotfiles_templates if t.name == template]
            if not dotfiles_templates:
                console.print(f"[red]Template '{template}' not found[/red]")
                raise typer.Exit(1)

        # Check status of all dotfiles templates
        status_data = []

        for template in dotfiles_templates:
            template_status = {
                "name": template.name,
                "description": template.description,
                "installed_links": [],
                "broken_links": [],
                "missing_links": [],
            }

        # Get expected symlinks for this template
        expected_links = dotfiles_manager.expected_symlinks_for_template(template, repo_cache_dir)

        for link in expected_links:
            if link.target.exists():
                if link.target.is_symlink():
                    actual_source = link.target.resolve()
                    if actual_source == link.source:
                        template_status["installed_links"].append(
                            {"target": str(link.target), "source": str(link.source), "status": "ok"}
                        )
                    else:
                        template_status["broken_links"].append(
                            {
                                "target": str(link.target),
                                "source": str(link.source),
                                "actual_source": str(actual_source),
                                "status": "wrong_target",
                            }
                        )
                else:
                    template_status["broken_links"].append(
                        {"target": str(link.target), "source": str(link.source), "status": "not_symlink"}
                    )
            else:
                template_status["missing_links"].append(
                    {"target": str(link.target), "source": str(link.source), "status": "missing"}
                )

            status_data.append(template_status)

        # Output results
        if context.output_format == "json":
            render_json({"templates": status_data})
        else:
            render_text_status(status_data, context.config.default_repo_url, repo_cache_dir, verbose=context.verbose)

    except Exception as e:
        handle_command_error(e)
