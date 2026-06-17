import os
import sys
import json
import base64
import argparse

import mimetypes

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from modules.consts import BASE_DIR
from modules.utils import clickable_path, open_browser, write_config, remove_from_config


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
    if not Path(BASE_DIR / ("data/" + args.data_file + ".json")).exists():
        print(f"Error: file '{args.data_file}' not found")
        sys.exit(1)

    with open(BASE_DIR / ("data/" + args.data_file + ".json"),
              encoding="utf-8") as f:
        data = json.load(f)

    data["position"] = args.position

    output_file = generate_html(data, config)
    
    write_config(config, "last_file", output_file)

    print(f"Done: {clickable_path(output_file)}")

    # Open browser
    open_browser(config, output_file)


def command_data(args: argparse.Namespace, config: dict):
    if args.data_file is None and not args.reset:
        print(f"Current name of resume data file: {\
            config.get("data_file", "data")}")

    elif args.data_file is not None:
        write_config(config, "data_file", args.data_file)
        print(f"Name of data file set to: {args.data_file}")

    elif args.reset:
        try:
            remove_from_config(config, "data_file")
            print(f"Name of data file is reset to default: data")
        except KeyError:
            print(f"Name of data file is already default: data")


def command_output(args: argparse.Namespace, config: dict):
    if args.output_path is None and not args.reset:
        print(f"Current path to output data: {\
            clickable_path(config.get("output_path", BASE_DIR / "output/"))}")

    elif args.output_path is not None:
        write_config(config, "output_path", args.output_path)
        print(f"Output path set to: {args.output_path}")

    elif args.reset:
        try:
            remove_from_config(config, "output_path")
            print(f"Output path is reset to default: {\
                clickable_path(BASE_DIR / "output/")}")
        except KeyError:
            print(f"Output path is already default: {\
                clickable_path(BASE_DIR / "output/")}")


def command_template(args: argparse.Namespace, config: dict):
    templates_dir = BASE_DIR / "templates"

    if args.template_name is None and not args.reset:
        current = config.get("template", "classic")
        available = sorted(
            p.stem for p in templates_dir.glob("*.html")
        )
        print(f"Current template: {current}")
        print(f"Available templates: {', '.join(available)}")

    elif args.template_name is not None:
        template_file = templates_dir / f"{args.template_name}.html"
        if not template_file.exists():
            available = sorted(p.stem for p in templates_dir.glob("*.html"))
            print(f"Error: template '{args.template_name}' not found.")
            print(f"Available templates: {', '.join(available)}")
            sys.exit(1)
        write_config(config, "template", args.template_name)
        print(f"Template set to: {args.template_name}")

    elif args.reset:
        try:
            remove_from_config(config, "template")
            print("Template is reset to default: classic")
        except KeyError:
            print("Template is already default: classic")


def command_last(config: dict):
    last_file = config.get("last_file")
    if last_file and Path(last_file).exists():
        print(f"Last generated file: {clickable_path(last_file)}")
        open_browser(config, last_file)
    else:
        print("No last generated file found.")


def command_search(args: argparse.Namespace, config: dict):
    output_dir = config.get("output_path", BASE_DIR / "output/")
    position = args.position.replace(" ", "_").lower()
    pattern = f"resume_*{position}*.html"

    found_files = sorted(Path(output_dir).glob(pattern), key=os.path.getmtime, reverse=True)

    if len(found_files) > 1:
        print(f"Found {len(found_files)} file(s) for position '{args.position}':")
        for file in found_files:
            print(f"- {clickable_path(file)}")
    elif len(found_files) == 1:
        print(f"Found 1 file for position '{args.position}': {clickable_path(found_files[0])}")
        open_browser(config, found_files[0])
    else:
        print(f"No files found for position '{args.position}'.")


def command_browser(args: argparse.Namespace, config: dict):
    state = args.state.lower()
    if state == "on":
        write_config(config, "auto_open", True)
        print("Auto-open in browser is turned ON.")
    elif state == "off":
        write_config(config, "auto_open", False)
        print("Auto-open in browser is turned OFF.")


def command_edit(args: argparse.Namespace, config: dict):
    # data_file = config.get("data_file", "data")
    # target_file = BASE_DIR / f"data/{args.data}.json"
    # if not target_file.exists():
    #     print(f"Error: data file '{args.data}' not found in 'data/' directory.")
    #     sys.exit(1)
    pass


def command_new(args: argparse.Namespace, config: dict):
    pass


def command_remove(args: argparse.Namespace, config: dict):
    target_file = BASE_DIR / f"data/{args.data}.json"
    if not target_file.exists():
        print(f"Error: data file '{args.data}' not found in 'data/' directory.")
        sys.exit(1)

    approve = input(f"Are you sure you want to remove '{args.data}'? (y/N): ")
    if approve.lower() != 'y':
        print("Operation cancelled.")
        return
    try:
        os.remove(target_file)
        print(f"Data file '{args.data}' has been removed.")
    except Exception as e:
        print(f"Error removing data file '{args.data}': {e}")
