import os
import sys
import json
import base64
import argparse
import subprocess

import mimetypes

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from modules.consts import BASE_DIR
from modules.utils import clickable_path, open_browser, write_config, remove_from_config
from modules.colored_text import print_error, print_success, print_warning, print_info, Color


def generate_html(data: dict, config: dict) -> str:
    with open(BASE_DIR / "locales.json", encoding="utf-8") as f:
        locales = json.load(f)

    lang = data.get("lang", "en")
    t = locales.get(lang, locales["en"])

    photo_data_uri = None
    photo_path = BASE_DIR / ("data/" + data.get("photo", "photo.png"))
    if photo_path and Path(photo_path).exists():
        mime, _ = mimetypes.guess_type(photo_path)
        with open(photo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        photo_data_uri = f"data:{mime};base64,{encoded}"

    template_name = config.get("template", "classic")
    templates_dir = BASE_DIR / "templates"

    template_file = templates_dir / f"{template_name}.html"
    if not template_file.exists():
        print(f"Error: template '{template_name}' not found in {templates_dir}")
        sys.exit(1)

    env = Environment(loader=FileSystemLoader(templates_dir))
    html = env.get_template(f"{template_name}.html").render(
        **data,
        photo_data_uri=photo_data_uri,
        t=t
    )

    output_dir = config.get("output_path", BASE_DIR / "output/")
    os.makedirs(output_dir, exist_ok=True)

    position = data.get("position", "resume").replace(" ", "_").lower()
    output_file = os.path.join(output_dir, f"resume_{position}.html")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    return output_file


def command_make(args: argparse.Namespace, config: dict):
    if args.data_file is None:
        print_error("Error: no data file specified. Specify a data file with --data_file or set a default data file using the 'data' command.")
        sys.exit(1)
    if not Path(BASE_DIR / ("data/" + args.data_file + ".json")).exists():
        print_error(f"Error: file '{args.data_file}' not found")
        sys.exit(1)

    with open(BASE_DIR / ("data/" + args.data_file + ".json"),
              encoding="utf-8") as f:
        data = json.load(f)

    data["position"] = args.position

    output_file = generate_html(data, config)
    
    write_config(config, "last_file", output_file)

    print_success(f"Done: {clickable_path(output_file)}")

    # Open browser
    open_browser(config, output_file)


def command_data(args: argparse.Namespace, config: dict):
    if args.data_file is None:
        if args.list:
            data_dir = BASE_DIR / "data"
            data_files = sorted(p.stem for p in data_dir.glob("*.json"))
            print_info(f"Available data files:\n{'\n'.join(f" - {f}" for f in data_files)}")
        else:
            print_info(f"Current name of resume data file: {\
                Color.green(config.get("data_file", Color.red("NOT SET")))}")

    else:
        write_config(config, "data_file", args.data_file)
        print_success(f"Name of current data file set to: {args.data_file}")


def command_output(args: argparse.Namespace, config: dict):
    if args.output_path is None and not args.reset:
        print_info(f"Current path to output data: {\
            clickable_path(config.get("output_path", BASE_DIR / "output/"))}")

    elif args.output_path is not None:
        write_config(config, "output_path", args.output_path)
        print_success(f"Output path set to: {args.output_path}")

    elif args.reset:
        try:
            remove_from_config(config, "output_path")
            print_success(f"Output path is reset to default: {\
                clickable_path(BASE_DIR / "output/")}")
        except KeyError:
            print_info(f"Output path is already default: {\
                clickable_path(BASE_DIR / "output/")}")


def command_template(args: argparse.Namespace, config: dict):
    templates_dir = BASE_DIR / "templates"

    if args.template_name is None and not args.reset:
        current = config.get("template", "classic")
        available = sorted(
            p.stem for p in templates_dir.glob("*.html")
        )
        print_success(f"Current template: {current}")
        print_info(f"Available templates: {', '.join(available)}")

    elif args.template_name is not None:
        template_file = templates_dir / f"{args.template_name}.html"
        if not template_file.exists():
            available = sorted(p.stem for p in templates_dir.glob("*.html"))
            print_error(f"Error: template '{args.template_name}' not found.")
            print_info(f"Available templates: {', '.join(available)}")
            sys.exit(1)
        write_config(config, "template", args.template_name)
        print_success(f"Template set to: {args.template_name}")

    elif args.reset:
        try:
            remove_from_config(config, "template")
            print_success(f"Template is reset to default: classic")
        except KeyError:
            print_info(f"Template is already default: classic")


def command_last(config: dict):
    last_file = config.get("last_file")
    if last_file and Path(last_file).exists():
        print_info(f"Last generated file: {clickable_path(last_file)}")
        open_browser(config, last_file)
    else:
        print_warning("No last generated file found.")


def command_search(args: argparse.Namespace, config: dict):
    output_dir = config.get("output_path", BASE_DIR / "output/")
    position = args.position.replace(" ", "_").lower()
    pattern = f"resume_*{position}*.html"

    found_files = sorted(Path(output_dir).glob(pattern), key=os.path.getmtime, reverse=True)

    if len(found_files) > 1:
        print_success(f"Found {len(found_files)} file(s) for position '{args.position}':")
        for file in found_files:
            print(f"- {clickable_path(file)}")
    elif len(found_files) == 1:
        print_info(f"Found 1 file for position '{args.position}': {clickable_path(found_files[0])}")
        open_browser(config, found_files[0])
    else:
        print_warning(f"No files found for position '{args.position}'.")


def command_show(args: argparse.Namespace, config: dict):
    def format_data(value, indent=0):
        indent_str = " " * indent
        list_char = Color.yellow("-")
        if isinstance(value, dict):
            if not value:
                return f"{indent_str}{Color.red('NOT SET')}"
            lines = []
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent_str}{Color.blue(key.capitalize())}:")
                    lines.append(format_data(item, indent + 2))
                elif item is None or (isinstance(item, str) and item.strip() == ""):
                    lines.append(f"{indent_str}{Color.blue(key.capitalize())}: {Color.red('NOT SET')}")
                else:
                    lines.append(f"{indent_str}{Color.blue(key.capitalize())}: {item}")
            return "\n".join(lines)
        if isinstance(value, list):
            if not value:
                return f"{indent_str}{Color.red('NOT SET')}"
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(format_data(item, indent + 2))
                    lines.append("")
                elif item is None or (isinstance(item, str) and item.strip() == ""):
                    lines.append(f"{indent_str}{list_char} {Color.red('NOT SET')}")
                else:
                    lines.append(f"{indent_str}{list_char} {item}")
            return "\n".join(lines)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return f"{indent_str}{Color.red('NOT SET')}"
        return f"{indent_str}{value}"

    data_file_name = args.data_file or config.get("data_file", "data")
    data_file = BASE_DIR / f"data/{data_file_name}.json"
    if not data_file.exists():
        print(f"Error: data '{data_file_name}' does not exist.")
        sys.exit(1)

    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)

    print(f"{Color.magenta(str(f'---------- {data_file_name.upper()} ----------'))}\n{format_data(data)}")


def command_browser(args: argparse.Namespace, config: dict):
    state = args.state.lower()
    if state == "on":
        write_config(config, "auto_open", True)
        print_success("Auto-open in browser is turned ON.")
    elif state == "off":
        write_config(config, "auto_open", False)
        print_success("Auto-open in browser is turned OFF.")


def command_edit(args: argparse.Namespace, config: dict):
    data_file_name = args.data or config.get("data_file", "data")
    target_file = BASE_DIR / f"data/{data_file_name}.json"
    if not target_file.exists():
        print_warning(f"Error: data file '{data_file_name}' does not exist.")
        sys.exit(1)
    try:
        if sys.platform == "win32":
            subprocess.run(["notepad", str(target_file)])
        else:
            subprocess.run(["nano", str(target_file)])
    except Exception as e:
        print_error(f"Error opening editor: {e}")
        sys.exit(1)


def command_new(args: argparse.Namespace, config: dict):
    new_file_name = args.data
    target_file = BASE_DIR / f"data/{new_file_name}.json"
    if target_file.exists():
        print_warning(f"Error: data '{new_file_name}' already exists.")
        sys.exit(1)

    if args.copy:
        source_file = BASE_DIR / f"data/{args.copy}.json"
        if not source_file.exists():
            print_warning(f"Error: source data '{args.copy}' does not exist.")
            sys.exit(1)
        with open(source_file, encoding="utf-8") as f:
            data = json.load(f)
    else:
        source_file = BASE_DIR / f"template.json"
        with open(source_file, encoding="utf-8") as f:
            data = json.load(f)

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print_success(f"New data file '{new_file_name}' has been created.")
    
    command_data(argparse.Namespace(data_file=new_file_name, list=False), config)


def command_remove(args: argparse.Namespace, config: dict):
    target_file = BASE_DIR / f"data/{args.data}.json"
    if not target_file.exists():
        print_warning(f"Error: data file '{args.data}' does not exist.")
        sys.exit(1)

    approve = input(f"{Color.yellow('Are you sure you want to remove \'' + args.data + '\'? (y/N): ')}")
    if approve.lower() != 'y':
        print_warning("Operation cancelled.")
        return
    try:
        os.remove(target_file)
        print_success(f"Data '{args.data}' has been removed.")
        if config.get("data_file") == args.data:
            remove_from_config(config, "data_file")
    except Exception as e:
        print_error(f"Error removing data file '{args.data}': {e}")
