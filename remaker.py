import os
import sys
import json
import base64
import argparse
import mimetypes

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


VERSION = "0.0.1"


def generate_html(data: dict, config: dict) -> str:
    with open("locales.json", encoding="utf-8") as f:
        locales = json.load(f)

    lang = config.get("lang", "en")
    t = locales.get(lang, locales["en"])

    css_path = Path(config.get("style_path", "style.css"))
    if not css_path.exists():
        print(f"Warning: style file '{css_path}' not found")
        css = ""
    else:
        css = css_path.read_text(encoding="utf-8")

    photo_data_uri = None
    photo_path = data.get("photo")
    if photo_path and Path(photo_path).exists():
        mime, _ = mimetypes.guess_type(photo_path)
        with open(photo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        photo_data_uri = f"data:{mime};base64,{encoded}"

    env = Environment(loader=FileSystemLoader("."))
    html = env.get_template("template.html").render(
        **data,
        css=css,
        photo_data_uri=photo_data_uri,
        t=t
    )

    output_dir = config["output_path"]
    os.makedirs(output_dir, exist_ok=True)

    position = data.get("position", "resume").replace(" ", "_").lower()
    output_file = os.path.join(output_dir, f"resume_{position}.html")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    return output_file


def command_create(args: argparse.Namespace, config: dict):
    if not Path(args.data_path).exists():
        print(f"Error: file '{args.data_path}' not found")
        sys.exit(1)

    with open(args.data_path, encoding="utf-8") as f:
        data = json.load(f)

    data["position"] = args.position

    output_file = generate_html(data, config)
    print(f"Done: {output_file}")


def command_lang(args: argparse.Namespace, config: dict):
    if args.language is None:
        print(f"Current language: {config.get("lang", "en")}")
    else:
        config["lang"] = args.language
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"Language set to: {args.language}")


def command_data(args: argparse.Namespace, config: dict):
    if args.data_path is None:
        print(f"Current path to resume data: {config.get("data_path", "data/data.json")}")
    else:
        config["data_path"] = args.data_path
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"Data path set to: {args.data_path}")
    


def build_parser(config: dict) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="remaker",
        description="Resume generator"
    )
    parser.add_argument("--version", action="version", version=VERSION)

    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("make", help="Make resume from data file")
    create_parser.add_argument("position", help="Job position name")
    create_parser.add_argument("-dp", "--data_path", default=f"{config.get("data_path", "data/data.json")}", help=f"Path to data file")

    lang_parser = subparsers.add_parser("lang", help="Change resume language (en/ru)")
    lang_parser.add_argument("language", nargs="?", help="Resume language (en/ru)", default=None)
    
    data_parser = subparsers.add_parser("data", help=f"Set path to data file")
    data_parser.add_argument("data_path", nargs="?", help="Path to data file", default=None)

    return parser


def main():
    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)

    parser = build_parser(config)
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "make":
        command_create(args, config)
    elif args.command == "lang":
        command_lang(args, config)
    elif args.command == "data":
        command_data(args, config)


if __name__ == "__main__":
    main()
