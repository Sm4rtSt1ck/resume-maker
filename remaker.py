import json
import rich_click as click

from modules.commands import (
    command_make, command_data, command_output, command_template,
    command_last, command_search, command_show, command_browser, command_pdf,
    command_rename, command_edit, command_new, command_remove,
    command_export, command_import, command_convert, command_config, command_list,
)
from modules.consts import VERSION, BASE_DIR

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = False
click.rich_click.COMMAND_GROUPS = {
    "remaker": [
        {
            "name": "Resume generation",
            "commands": ["make", "convert", "last", "search", "list"],
        },
        {
            "name": "Data management",
            "commands": ["data", "new", "edit", "remove", "rename", "show", "export", "import"],
        },
        {
            "name": "Configuration",
            "commands": ["output", "template", "browser", "pdf", "config"],
        },
    ]
}


def _load_config() -> dict:
    config_path = BASE_DIR / "config.json"
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


@click.group()
@click.version_option(VERSION, prog_name="remaker")
@click.pass_context
def cli(ctx: click.Context):
    """HTML resume generator based on Jinja2 templates.

    Quickly make tailored resumes for different job positions
    by swapping out data files.
    """
    ctx.ensure_object(dict)
    ctx.obj = _load_config()


# ─── Resume generation ──────────────────────────────────────────────────────

@cli.command()
@click.argument("position")
@click.option("-d", "--data-file", default=None, help="Data name (overrides default)")
@click.option("-t", "--template", default=None, help="Template (overrides default)")
@click.pass_obj
def make(config: dict, position: str, data_file: str | None, template: str | None):
    """Generate a resume HTML (and optionally PDF) for a job POSITION."""
    command_make(position, data_file or config.get("data_file"), template or config.get("template"), config)


@cli.command()
@click.option("-n", "--name", default=None, help="Vacancy name or path to HTML file")
@click.option("-o", "--output-path", "output_path", default=None, help="Output directory for the PDF")
@click.pass_obj
def convert(config: dict, name: str | None, output_path: str | None):
    """Convert an HTML resume to PDF."""
    command_convert(name or config.get("last_file"), output_path, config)


@cli.command()
@click.pass_obj
def last(config: dict):
    """Open the last generated resume in a browser."""
    command_last(config)


@cli.command()
@click.argument("position")
@click.pass_obj
def search(config: dict, position: str):
    """Find generated resume files matching a POSITION name."""
    command_search(position, config)


@cli.command(name="list")
@click.argument("file_type", metavar="TYPE", required=False, default="html",
                type=click.Choice(["html", "pdf", "all"]))
@click.pass_obj
def list_cmd(config: dict, file_type: str):
    """List generated resume files. TYPE is html (default), pdf, or all."""
    command_list(file_type, config)


# ─── Data management ────────────────────────────────────────────────────────

@cli.command()
@click.argument("data_file", metavar="NAME", required=False, default=None)
@click.pass_obj
def data(config: dict, data_file: str | None):
    """Set the default data file to NAME, or show available files."""
    command_data(data_file, config)


@cli.command()
@click.argument("name")
@click.option("-c", "--copy", default=None, metavar="SOURCE", help="Copy from an existing data file")
@click.pass_obj
def new(config: dict, name: str, copy: str | None):
    """Create a new data file called NAME."""
    command_new(name, copy, config)


@cli.command()
@click.argument("name", required=False, default=None)
@click.pass_obj
def edit(config: dict, name: str | None):
    """Open a data file in the system editor."""
    command_edit(name, config)


@cli.command()
@click.argument("name")
@click.pass_obj
def remove(config: dict, name: str):
    """Delete a data file."""
    command_remove(name, config)


@cli.command()
@click.argument("old_name")
@click.argument("new_name")
@click.pass_obj
def rename(config: dict, old_name: str, new_name: str):
    """Rename a data file from OLD_NAME to NEW_NAME."""
    command_rename(old_name, new_name, config)


@cli.command()
@click.argument("name", required=False, default=None)
@click.pass_obj
def show(config: dict, name: str | None):
    """Display the contents of a data file."""
    command_show(name, config)


@cli.command()
@click.argument("path")
@click.argument("names", metavar="[NAME]...", nargs=-1)
@click.pass_obj
def export(config: dict, path: str, names: tuple[str, ...]):
    """Export data files to PATH. Pass / to export all."""
    command_export(path, names, config)


@cli.command(name="import")
@click.argument("path")
def import_cmd(path: str):
    """Import data files from PATH (file or directory)."""
    command_import(path)


# ─── Configuration ──────────────────────────────────────────────────────────

@cli.command()
@click.argument("output_path", metavar="PATH", required=False, default=None)
@click.option("-r", "--reset", is_flag=True, help="Reset to default")
@click.pass_obj
def output(config: dict, output_path: str | None, reset: bool):
    """Set the output directory to PATH, or show the current value."""
    command_output(output_path, reset, config)


@cli.command()
@click.argument("name", required=False, default=None)
@click.option("-r", "--reset", is_flag=True, help="Reset to default (classic)")
@click.pass_obj
def template(config: dict, name: str | None, reset: bool):
    """Set the active HTML template to NAME, or list available templates."""
    command_template(name, reset, config)


@cli.command()
@click.argument("state", required=False, default=None,
                type=click.Choice(["on", "off"]))
@click.pass_obj
def browser(config: dict, state: str | None):
    """Toggle auto-open in browser (on/off), or show current state."""
    command_browser(state, config)


@cli.command()
@click.argument("state", required=False, default=None,
                type=click.Choice(["on", "off"]))
@click.pass_obj
def pdf(config: dict, state: str | None):
    """Toggle auto-conversion to PDF (on/off), or show current state."""
    command_pdf(state, config)


@cli.command()
@click.pass_obj
def config(cfg: dict):
    """Show all configuration as a table."""
    command_config(cfg)


def main():
    cli(prog_name="remaker")


if __name__ == "__main__":
    main()
