import os
import sys
import json
import base64
import argparse

import mimetypes
import webbrowser
import subprocess

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from modules.consts import BASE_DIR
from modules.utils import clickable_path, write_config, remove_from_config


def generate_html(data: dict, config: dict) -> str:
    with open(BASE_DIR / "locales.json", encoding="utf-8") as f:
        locales = json.load(f)

    lang = data.get("lang", "en")
    t = locales.get(lang, locales["en"])

    css_path = BASE_DIR / config.get("style_path", "style.css")
    if not css_path.exists():
        print(f"Warning: style file '{css_path}' not found")
        css = ""
    else:
        css = css_path.read_text(encoding="utf-8")

    photo_data_uri = None
    photo_path = BASE_DIR / ("data/" + data.get("photo", "photo.png"))
    if photo_path and Path(photo_path).exists():
        mime, _ = mimetypes.guess_type(photo_path)
        with open(photo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        photo_data_uri = f"data:{mime};base64,{encoded}"

    env = Environment(loader=FileSystemLoader(BASE_DIR))
    html = env.get_template("template.html").render(
        **data,
        css=css,
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

    print(f"Done: {clickable_path(output_file)}")

    # Open browser
    path_obj = Path(output_file).resolve()
    if sys.platform == 'win32':
        os.startfile(str(path_obj))
    else:
        file_url = path_obj.as_uri()
        if sys.platform == 'darwin':
            subprocess.Popen(['open', file_url])
        else:
            try:
                subprocess.Popen(['xdg-open', file_url])
            except OSError:
                webbrowser.open(file_url)


def command_data(args: argparse.Namespace, config: dict):
    if args.data_file is None and not args.reset:
        print(f"Current name of resume data file: {
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
        print(f"Current path to output data: {
            clickable_path(config.get("output_path", BASE_DIR / "output/"))}")

    elif args.output_path is not None:
        write_config(config, "output_path", args.output_path)
        print(f"Output path set to: {args.output_path}")

    elif args.reset:
        try:
            remove_from_config(config, "output_path")
            print(f"Output path is reset to default: {
                clickable_path(BASE_DIR / "output/")}")
        except KeyError:
            print(f"Output path is already default: {
                clickable_path(BASE_DIR / "output/")}")
