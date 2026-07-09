import os
import re
import sys
import json
import base64
import shutil
import datetime
import mimetypes

import yaml

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.markup import escape
from rich.prompt import Confirm

from modules.html_to_pdf import html_to_pdf
from modules.consts import BASE_DIR
from modules.defaults import CONFIG_DEFAULTS
from modules.utils import (
    clickable_path, open_browser, write_config, remove_from_config,
    get_photo_from_resume, console,
    show_error, show_warning, show_success, show_info, show_cancelled,
)


def command_make(position: str, data_file: str | None, template: str | None, config: dict):
    if data_file is None:
        show_error("No data file specified. Use [highlight]--data-file[/] or set a default with the [highlight]data[/] command.")
        sys.exit(1)
    if not Path(BASE_DIR / "data" / f"{data_file}.json").exists():
        show_error(f"File '[bold]{escape(data_file)}[/]' not found.")
        sys.exit(1)

    def generate_html(data: dict, template: str, config: dict) -> Path:
        with open(BASE_DIR / "locales.yml", encoding="utf-8") as f:
            locales = yaml.safe_load(f)

        lang = data.get("lang", "en")
        t = locales.get(lang, locales["en"])

        photo_data_uri = None
        photo_path = BASE_DIR / "data" / data.get("photo", "photo.png")
        if Path(photo_path).exists() or Path(BASE_DIR / "data/popcat.png").exists():
            if not Path(photo_path).exists():
                show_warning(f"Photo '[bold]{escape(str(photo_path))}[/]' not found — using popcat instead.")
                photo_path = BASE_DIR / "data/popcat.png"
            mime, _ = mimetypes.guess_type(photo_path)
            with open(photo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            photo_data_uri = f"data:{mime};base64,{encoded}"

        templates_dir = BASE_DIR / "templates"

        template_file = templates_dir / f"{template}.html"
        if not template_file.exists():
            show_error(f"Template [highlight]{escape(template)}[/] not found in {escape(str(templates_dir))}")
            sys.exit(1)

        env = Environment(loader=FileSystemLoader(templates_dir))
        html = env.get_template(f"{template}.html").render(
            **data,
            photo_data_uri=photo_data_uri,
            t=t
        )

        output_dir = config.get("output_path", CONFIG_DEFAULTS["output_path"])
        os.makedirs(output_dir, exist_ok=True)

        position = data.get("position", "resume").replace(" ", "_").lower()
        output_file = Path(output_dir) / f"resume_{position}.html"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        return output_file


    with open(BASE_DIR / "data" / f"{data_file}.json", encoding="utf-8") as f:
        data = json.load(f)

    data["position"] = position

    output_file = generate_html(data, template or CONFIG_DEFAULTS["template"], config)
    write_config(config, "last_file", output_file)

    show_success(f"HTML: {clickable_path(output_file)}")
    open_browser(config, output_file)

    if config.get("convert_to_pdf", CONFIG_DEFAULTS["convert_to_pdf"]):
        with console.status("[blue]Converting to PDF...[/]", spinner="dots"):
            pdf_path = output_file.with_suffix(".pdf")
            result = html_to_pdf(output_file, pdf_path)
        if result:
            show_success(f"PDF: {clickable_path(pdf_path)}")
        else:
            show_warning("No Chromium-based browser found — PDF generation skipped.")


def command_data(data_file: str | None, config: dict):
    if data_file is None:
        data_dir = BASE_DIR / "data"
        entries = sorted(p.stem for p in data_dir.glob("*.json"))

        current = config.get("data_file")
        if current is not None and current in entries:
            entries.remove(current)
            entries.append(f"[green]{escape(current)}[/] (current)")

        console.rule("[bold magenta]Available data files[/]", style="dim magenta")
        for entry in entries:
            console.print(f"  [cyan]•[/] {entry}")
        if current is None:
            show_warning("No default data file is set. Use [bold]data NAME[/] to set one.")

    elif Path.exists(BASE_DIR / "data" / f"{data_file}.json"):
        write_config(config, "data_file", data_file)
        show_success(f"Default data file set to [bold]{escape(data_file)}[/]", title="Updated")
    else:
        show_error(f"Data '[bold]{escape(data_file)}[/]' does not exist.")
        sys.exit(1)


def command_output(output_path: str | None, reset: bool, config: dict):
    if output_path is None and not reset:
        show_info(clickable_path(config.get("output_path", CONFIG_DEFAULTS["output_path"])), title="Output path")

    elif output_path is not None:
        write_config(config, "output_path", output_path)
        show_success(f"Output path set to [bold]{escape(output_path)}[/]", title="Updated")

    elif reset:
        try:
            remove_from_config(config, "output_path")
            show_success(
                f"Output path reset to default: {clickable_path(CONFIG_DEFAULTS['output_path'])}",
                title="Reset",
            )
        except KeyError:
            show_info(
                f"Output path is already the default: {clickable_path(CONFIG_DEFAULTS['output_path'])}",
                title="No change",
            )


def command_template(template_name: str | None, reset: bool, config: dict):
    templates_dir = BASE_DIR / "templates"

    if template_name is None and not reset:
        files = sorted(p.stem for p in templates_dir.glob("*.html"))

        current = config.get("template", CONFIG_DEFAULTS["template"])
        if current in files:
            files.remove(current)
            files.append(f"[green]{escape(current)}[/] (current)")
        else:
            show_warning("Current template is [null]NOT SET[/].")

        console.rule("[bold magenta]Available templates[/]", style="dim magenta")
        for f in files:
            console.print(f"  [cyan]•[/] {f}")

    elif template_name is not None:
        template_file = templates_dir / f"{template_name}.html"
        if not template_file.exists():
            available = ", ".join(sorted(p.stem for p in templates_dir.glob("*.html")))
            show_error(
                f"Template [highlight]{escape(template_name)}[/] not found.\n"
                f"Available: [info]{escape(available)}[/]"
            )
            sys.exit(1)
        write_config(config, "template", template_name)
        show_success(f"Template set to [highlight]{escape(template_name)}[/]", title="Updated")

    elif reset:
        try:
            remove_from_config(config, "template")
            show_success(
                f"Template reset to default: [highlight]{escape(CONFIG_DEFAULTS['template'])}[/]",
                title="Reset",
            )
        except KeyError:
            show_info(
                f"Template is already the default: [highlight]{escape(CONFIG_DEFAULTS['template'])}[/]",
                title="No change",
            )


def command_last(config: dict):
    last_file = config.get("last_file")
    if last_file and Path(last_file).exists():
        show_info(clickable_path(last_file), title="Last generated file")
        open_browser(config, last_file)
    else:
        show_warning("No last generated file found.")


def command_search(position: str, config: dict):
    output_dir = config.get("output_path", CONFIG_DEFAULTS["output_path"])
    pattern = f"resume_*{position.replace(' ', '_').lower()}*.html"
    found = sorted(Path(output_dir).glob(pattern), key=os.path.getmtime, reverse=True)

    if not found:
        show_warning(f"No files found for position [highlight]{escape(position)}[/].")
        return

    lines = "\n".join(f"  [cyan]•[/] {clickable_path(f)}" for f in found)
    show_info(lines, title=f"Found {len(found)} file(s) for '{escape(position)}'")

    if len(found) == 1:
        open_browser(config, found[0])


def command_show(data_file: str | None, config: dict):
    def format_data(value, indent=0):
        pad = " " * indent
        if isinstance(value, dict):
            if not value:
                return f"{pad}[null]NOT SET[/]"
            lines = []
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"{pad}[info]{escape(key.capitalize())}[/]:")
                    lines.append(format_data(item, indent + 2))
                elif item is None or (isinstance(item, str) and item.strip() == ""):
                    lines.append(f"{pad}[info]{escape(key.capitalize())}[/]: [null]NOT SET[/]")
                else:
                    lines.append(f"{pad}[info]{escape(key.capitalize())}[/]: {escape(str(item))}")
            return "\n".join(lines)
        if isinstance(value, list):
            if not value:
                return f"{pad}[null]NOT SET[/]"
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(format_data(item, indent + 2))
                    lines.append("")
                elif item is None or (isinstance(item, str) and item.strip() == ""):
                    lines.append(f"{pad}[info]•[/] [null]NOT SET[/]")
                else:
                    lines.append(f"{pad}[info]•[/] {escape(str(item))}")
            return "\n".join(lines)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return f"{pad}[null]NOT SET[/]"
        return f"{pad}{escape(str(value))}"

    name = data_file or config.get("data_file", "data")
    path = BASE_DIR / f"data/{name}.json"
    if not path.exists():
        show_error(f"Data [highlight]{escape(name)}[/] does not exist.")
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    console.print(Panel(
        format_data(data),
        title=f"[bold frame]{escape(name.upper())}[/]",
        border_style="frame",
    ))


def command_browser(state: str | None, config: dict):
    if state is None:
        val = "enabled" if config.get("auto_open", CONFIG_DEFAULTS["auto_open"]) else "disabled"
        color = "green" if val == "enabled" else "red"
        show_info(f"Auto-open in browser is [{color}]{val}[/]", title="Browser")
        return
    write_config(config, "auto_open", state == "on")
    show_success(f"Auto-open in browser turned [highlight]{'ON' if state == 'on' else 'OFF'}[/]", title="Updated")


def command_pdf(state: str | None, config: dict):
    if state is None:
        val = "enabled" if config.get("convert_to_pdf", CONFIG_DEFAULTS["convert_to_pdf"]) else "disabled"
        color = "green" if val == "enabled" else "red"
        show_info(f"Auto-conversion to PDF is [{color}]{val}[/]", title="PDF")
        return
    write_config(config, "convert_to_pdf", state == "on")
    show_success(f"Auto-conversion to PDF turned [highlight]{'ON' if state == 'on' else 'OFF'}[/]", title="Updated")


def command_edit(data: str | None, config: dict):
    name = data or config.get("data_file", "data")
    target = BASE_DIR / f"data/{name}.json"
    if not target.exists():
        show_error(f"Data [highlight]{escape(name)}[/] does not exist.")
        sys.exit(1)

    try:
        with open(target, encoding="utf-8") as f:
            content = json.load(f)
        if not isinstance(content, dict):
            raise ValueError("root must be a JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        show_error(f"'[highlight]{escape(name)}[/]' is not a valid data file: {escape(str(e))}")
        sys.exit(1)

    from modules.editor import run_editor

    if run_editor(target):
        show_success(f"Saved {clickable_path(target)}")
    else:
        show_cancelled()


def command_rename(old_name: str, new_name: str, config: dict):
    old_path = BASE_DIR / f"data/{old_name}.json"
    new_path = BASE_DIR / f"data/{new_name}.json"

    if new_path.exists():
        show_error(f"'[highlight]{escape(new_name)}[/]' already exists. Choose another name.")
        sys.exit(1)

    if old_path.exists():
        old_path.rename(new_path)
        if config.get("data_file") == old_name:
            write_config(config, "data_file", new_name)
        show_success(
            f"[highlight]{escape(old_name)}[/] → [highlight]{escape(new_name)}[/]",
            title="Renamed",
        )
    else:
        show_error(f"'[highlight]{escape(old_name)}[/]' does not exist.")
        sys.exit(1)


def command_new(data: str, copy: str | None, config: dict):
    target = BASE_DIR / f"data/{data}.json"
    if target.exists():
        show_error(f"Data [highlight]{escape(data)}[/] already exists.")
        sys.exit(1)

    if copy:
        source = BASE_DIR / f"data/{copy}.json"
        if not source.exists():
            show_error(f"Source data [highlight]{escape(copy)}[/] does not exist.")
            sys.exit(1)
        with open(source, encoding="utf-8") as f:
            template_data = json.load(f)
    else:
        try:
            with open(BASE_DIR / "template.json", encoding="utf-8") as f:
                template_data = json.load(f)
        except FileNotFoundError:
            show_error("template.json not found. Please reinstall the application.")
            sys.exit(1)

    os.makedirs(BASE_DIR / "data/", exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(template_data, f, indent=4, ensure_ascii=False)

    show_success(f"Data file '[highlight]{escape(data)}[/]' created.", title="Created")
    command_data(data, config)


def command_remove(data: str, config: dict):
    target = BASE_DIR / f"data/{data}.json"
    if not target.exists():
        show_error(f"Data file [highlight]{escape(data)}[/] does not exist.")
        sys.exit(1)

    if not Confirm.ask(f"Remove [highlight]{escape(data)}[/]?", default=False):
        show_cancelled()
        return
    try:
        os.remove(target)
        show_success(f"Data [highlight]{escape(data)}[/] removed.", title="Removed")
        if config.get("data_file") == data:
            remove_from_config(config, "data_file")
    except Exception as e:
        show_error(f"Could not remove [highlight]{escape(data)}[/]: {escape(str(e))}")


def command_export(path: str, data: tuple[str, ...], config: dict):
    export_path = Path(path) / "REMAKER_EXPORT/"

    if data == ("/",):
        files_to_export = sorted((BASE_DIR / "data").iterdir())
        if not files_to_export:
            show_error("No data files found.")
            sys.exit(1)
    elif data:
        files_to_export = []
        for name in data:
            f = BASE_DIR / "data" / f"{name}.json"
            if not f.exists():
                show_error(f"Data [highlight]{escape(name)}[/] does not exist.")
                sys.exit(1)
            files_to_export.append(f)
            try:
                photo_name = get_photo_from_resume(f)
                pf = BASE_DIR / "data" / photo_name
                if pf.exists():
                    files_to_export.append(pf)
                else:
                    show_warning(f"Photo [highlight]{escape(photo_name)}[/] not found — skipping.")
            except (KeyError, json.JSONDecodeError):
                pass
    else:
        default = config.get("data_file")
        if not default:
            show_error("No data file specified and default is not set.")
            sys.exit(1)
        f = BASE_DIR / "data" / f"{default}.json"
        if not f.exists():
            show_error(f"Data [highlight]{escape(default)}[/] does not exist.")
            sys.exit(1)
        files_to_export = [f]
        try:
            photo_name = get_photo_from_resume(f)
            pf = BASE_DIR / "data" / photo_name
            if pf.exists():
                files_to_export.append(pf)
            else:
                show_warning(f"Photo [highlight]{escape(photo_name)}[/] not found — skipping.")
        except (KeyError, json.JSONDecodeError):
            pass

    if export_path.exists() and not export_path.is_dir():
        show_error(f"[highlight]{escape(str(export_path))}[/] already exists as a file.")
        sys.exit(1)
    os.makedirs(export_path, exist_ok=True)
    for src in files_to_export:
        shutil.copy2(src, export_path / src.name)

    show_success(clickable_path(export_path))


def command_import(path: str):
    source = Path(path)
    dest_dir = BASE_DIR / "data"
    image_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

    if not source.exists():
        show_error(f"[highlight]{escape(str(source))}[/] does not exist.")
        sys.exit(1)

    def _copy(src: Path, dst: Path):
        if dst.exists():
            if not Confirm.ask(f"[highlight]{escape(dst.name)}[/] already exists. Overwrite?", default=False):
                console.print(f"  [dim]Skipped:[/] {escape(src.name)}")
                return
        shutil.copy2(src, dst)
        console.print(f"  [green]Imported:[/] {clickable_path(dst)}")

    if source.is_dir():
        files = [f for f in source.iterdir()
                 if f.suffix.lower() in image_exts or f.suffix.lower() == ".json"]
        if not files:
            show_error(f"No JSON or image files found in [highlight]{escape(str(source))}[/].")
            sys.exit(1)
        for f in files:
            _copy(f, dest_dir / f.name)
    else:
        if not (source.suffix.lower() in image_exts or source.suffix.lower() == ".json"):
            show_error(f"[highlight]{escape(source.name)}[/] is not a JSON or image file.")
            sys.exit(1)
        _copy(source, dest_dir / source.name)
        if source.suffix.lower() == ".json":
            try:
                photo_name = get_photo_from_resume(source)
                photo_src = source.parent / photo_name
                if photo_src.exists():
                    _copy(photo_src, dest_dir / photo_src.name)
                else:
                    show_warning(f"Photo [highlight]{escape(photo_name)}[/] not found — skipping.")
            except (KeyError, json.JSONDecodeError):
                pass


def command_convert(name: str | None, output_path: str | None, config: dict):
    if name is None:
        show_error("No resume specified and no last generated file found.")
        sys.exit(1)

    if re.match(r'^[a-zA-Z0-9_]+$', name):
        html_path = BASE_DIR / f"output/resume_{name}.html"
    else:
        html_path = Path(name)

    if not html_path.exists():
        show_error(f"File not found:\n{escape(str(html_path))}")
        sys.exit(1)

    out = Path(output_path if output_path is not None else config.get("output_path", CONFIG_DEFAULTS["output_path"]))
    pdf_path = (out / Path(html_path).name).with_suffix(".pdf")

    if pdf_path.exists():
        if not Confirm.ask(f"[highlight]{escape(str(pdf_path))}[/] already exists. Overwrite?", default=False):
            show_cancelled()
            return

    with console.status("[blue]Converting to PDF...[/]", spinner="dots"):
        result = html_to_pdf(html_path, pdf_path)

    if result:
        show_success(clickable_path(pdf_path))
    else:
        show_error("No Chromium-based browser found — PDF generation aborted.")


def command_config(config: dict):
    last_file = config.get("last_file")
    if last_file and not Path(last_file).exists():
        last_val = f"[yellow]{escape(str(last_file))} (not found)[/]"
    elif last_file:
        last_val = clickable_path(last_file)
    else:
        last_val = "[red]NOT SET[/]"

    data_file = config.get("data_file")
    enabled = lambda v: "[green]enabled[/]" if v else "[red]disabled[/]"

    table = Table(show_header=True, border_style="frame", header_style="bold magenta", box=box.ROUNDED)
    table.add_column("COMMAND", style="bold cyan", no_wrap=True)
    table.add_column("PARAMETER", style="white")
    table.add_column("VALUE")

    table.add_row("template", "Template",               escape(config.get("template", CONFIG_DEFAULTS["template"])))
    table.add_row("data",     "Current data",           escape(data_file) if data_file else "[red]NOT SET[/]")
    table.add_row("browser",  "Auto-open in browser",   enabled(config.get("auto_open",      CONFIG_DEFAULTS["auto_open"])))
    table.add_row("pdf",      "Auto-conversion to PDF", enabled(config.get("convert_to_pdf", CONFIG_DEFAULTS["convert_to_pdf"])))
    table.add_row("output",   "Output path",            clickable_path(config.get("output_path", CONFIG_DEFAULTS["output_path"])))
    table.add_row("make",     "Last generated resume",  last_val)

    console.print(table)


def command_list(file_type: str, config: dict):
    output_path = Path(config.get("output_path", CONFIG_DEFAULTS["output_path"]))
    if not output_path.exists():
        show_info("Output directory does not exist yet.", title="List")
        return

    patterns = []
    if file_type in ("html", "all"):
        patterns.append("*.html")
    if file_type in ("pdf", "all"):
        patterns.append("*.pdf")

    files = sorted(f for pattern in patterns for f in output_path.glob(pattern))

    if not files:
        show_info(f"No [bold]{escape(file_type)}[/] files found in the output directory.", title="List")
        return

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("File", style="cyan")
    table.add_column("Type", justify="center", no_wrap=True)
    table.add_column("Size", justify="right", style="yellow", no_wrap=True)
    table.add_column("Created", style="dim", no_wrap=True)

    for file in files:
        size = file.stat().st_size / 1024
        created = datetime.datetime.fromtimestamp(file.stat().st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        label = "[blue]HTML[/]" if file.suffix == ".html" else "[red]PDF[/]"
        table.add_row(clickable_path(file), label, f"{size:.2f} KB", created)

    console.print(table)
