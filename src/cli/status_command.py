"""Status command implementation for installation status."""

import json
import logging

import typer
from rich import print
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
            expected_links = dotfiles_manager._get_symlinks_for_template(template, repo_cache_dir)

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
            print(json.dumps({"templates": status_data}, indent=2))
        else:
            # Text output
            console.print(f"Repository: {context.config.default_repo_url}")
            # Show sync status based on repository cache
            if repo_cache_dir.exists():
                console.print("Last sync: Repository is cached")
            else:
                console.print("Never synced")
            console.print("[bold]Installation Status:[/bold]")

            if not status_data:
                console.print("[yellow]No dotfiles templates found[/yellow]")
                return

            for template_status in status_data:
                name = template_status["name"]
                description = template_status["description"]
                installed = len(template_status["installed_links"])
                broken = len(template_status["broken_links"])
                missing = len(template_status["missing_links"])

                total = installed + broken + missing

                if total == 0:
                    console.print(f"\n[bold cyan]{name}[/bold cyan] - {description}")
                    console.print("  [yellow]No files to link[/yellow]")
                    continue

                status_color = "green" if broken == 0 and missing == 0 else "yellow" if broken == 0 else "red"
                console.print(f"\n[bold cyan]{name}[/bold cyan] - {description}")
                console.print(f"  [{status_color}]{installed}/{total} links active[/{status_color}]")

                if context.verbose or broken > 0 or missing > 0:
                    # Show detailed status
                    if template_status["installed_links"]:
                        console.print("  [green]✓ Active links:[/green]")
                        for link in template_status["installed_links"]:
                            console.print(f"    {link['target']} -> {link['source']}")

                    if template_status["broken_links"]:
                        console.print("  [red]✗ Broken links:[/red]")
                        for link in template_status["broken_links"]:
                            if link["status"] == "wrong_target":
                                console.print(
                                    f"    {link['target']} -> {link['actual_source']} (expected: {link['source']})"
                                )
                            else:
                                console.print(f"    {link['target']} (not a symlink)")

                    if template_status["missing_links"]:
                        console.print("  [yellow]○ Missing links:[/yellow]")
                        for link in template_status["missing_links"]:
                            console.print(f"    {link['target']} -> {link['source']}")

            # Summary
            total_templates = len(status_data)
            fully_installed = sum(
                1 for t in status_data if len(t["broken_links"]) == 0 and len(t["missing_links"]) == 0
            )

            console.print(f"\nSummary: {fully_installed}/{total_templates} templates fully installed")

    except Exception as e:
        handle_command_error(e)
