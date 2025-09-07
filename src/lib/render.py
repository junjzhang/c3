"""Lightweight rendering utilities for CLI output.

KISS: only two helpers exposed to keep a single output pathway.
 - render_json(data): user-visible JSON output via rich Console
 - render_text_status(...): text view for status command
"""

from __future__ import annotations

import json
from typing import Any
from pathlib import Path

from rich.table import Table
from rich.console import Console

console = Console()


def render_json(data: Any) -> None:
    """Render JSON data for the CLI user.

    Keeps one place to control formatting/highlighting.
    """
    # Avoid rich.print_json to prevent color codes in captured outputs when piping.
    console.print(json.dumps(data, indent=2, default=str))


def render_text_status(
    status_data: list[dict[str, Any]],
    repo_url: str | None,
    repo_cache_dir: Path,
    *,
    verbose: bool = False,
) -> None:
    """Render status information in text mode.

    Parameters
    - status_data: list of template status dicts with installed/broken/missing
    - repo_url: configured repository url
    - repo_cache_dir: local cache path
    - verbose: show details
    """
    console.print(f"Repository: {repo_url or '[red]Not configured[/red]'}")
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
        name = template_status.get("name", "")
        description = template_status.get("description", "")
        installed = len(template_status.get("installed_links", []))
        broken = len(template_status.get("broken_links", []))
        missing = len(template_status.get("missing_links", []))

        total = installed + broken + missing
        console.print(f"\n[bold cyan]{name}[/bold cyan] - {description}")

        if total == 0:
            console.print("  [yellow]No files to link[/yellow]")
            continue

        status_color = "green" if broken == 0 and missing == 0 else ("yellow" if broken == 0 else "red")
        console.print(f"  [{status_color}]{installed}/{total} links active[/{status_color}]")

        if verbose or broken > 0 or missing > 0:
            if template_status.get("installed_links"):
                console.print("  [green]✓ Active links:[/green]")
                for link in template_status["installed_links"]:
                    console.print(f"    {link['target']} -> {link['source']}")

            if template_status.get("broken_links"):
                console.print("  [red]✗ Broken links:[/red]")
                for link in template_status["broken_links"]:
                    if link.get("status") == "wrong_target":
                        console.print(f"    {link['target']} -> {link['actual_source']} (expected: {link['source']})")
                    else:
                        console.print(f"    {link['target']} (not a symlink)")

            if template_status.get("missing_links"):
                console.print("  [yellow]○ Missing links:[/yellow]")
                for link in template_status["missing_links"]:
                    console.print(f"    {link['target']} -> {link['source']}")

    total_templates = len(status_data)
    fully_installed = sum(
        1 for t in status_data if len(t.get("broken_links", ())) == 0 and len(t.get("missing_links", ())) == 0
    )
    console.print(f"\nSummary: {fully_installed}/{total_templates} templates fully installed")


def render_text_templates(templates: list[Any], *, detailed: bool = False) -> None:
    """Render template list in text mode grouped by type.

    Expects items exposing attributes: name, description, files, has_install_script(), is_dotfiles_template(),
    is_project_template().
    """
    console.print("[bold]Available templates:[/bold]")

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
