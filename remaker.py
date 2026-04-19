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


VERSION = "0.0.1"

BASE_DIR = Path(__file__).resolve().parent


def clickable_path(path: str | Path) -> str:
    abs_path = Path(path).resolve()
    uri = abs_path.as_uri()
    return f"\033]8;;{uri}\033\\{abs_path}\033]8;;\033\\"


def generate_html(data: dict, config: dict) -> str:
    with open(BASE_DIR / "locales.json", encoding="utf-8") as f:
        locales = json.load(f)

    lang = config.get("lang", "en")
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
    if not Path(BASE_DIR / ("data/" + args.data_path + ".json")).exists():
        print(f"Error: file '{args.data_path}' not found")
        sys.exit(1)

    with open(BASE_DIR / ("data/" + args.data_path + ".json"), encoding="utf-8") as f:
        data = json.load(f)

    data["position"] = args.position

    output_file = generate_html(data, config)
    print(f"Done: {clickable_path(output_file)}")

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


def write_config(config: dict, key: str, value) -> None:
    config[key] = value
    with open(BASE_DIR / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def remove_from_config(config: dict, key: str) -> None:
    config.pop(key)
    with open(BASE_DIR / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def command_lang(args: argparse.Namespace, config: dict):
    if args.language is None:
        print(f"Current language: {config.get("lang", "en")}")
    else:
        write_config(config, "lang", args.language)
        print(f"Language set to: {args.language}")


def command_data(args: argparse.Namespace, config: dict):
    if args.data_path is None and not args.reset:
        print(f"Current name of resume data file: {config.get("data_path", "data")}")
    elif args.data_path is not None:
        write_config(config, "data_path", args.data_path)
        print(f"Name of data file set to: {args.data_path}")
    elif args.reset:
        try:
            remove_from_config(config, "data_path")
            print(f"Name of data file is reset to default: data")
        except:
            print(f"Name of data file is already default: data")


def command_output(args: argparse.Namespace, config: dict):
    if args.output_path is None and not args.reset:
        print(f"Current path to output data: {clickable_path(config.get("output_path", BASE_DIR / "output/"))}")
    elif args.output_path is not None:
        write_config(config, "output_path", args.output_path)
        print(f"Output path set to: {args.output_path}")
    elif args.reset:
        try:
            remove_from_config(config, "output_path")
            print(f"Output path is reset to default: {clickable_path(BASE_DIR / "output/")}")
        except:
            print(f"Output path is already default: {clickable_path(BASE_DIR / "output/")}")


def build_parser(config: dict) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="remaker",
        description="Resume generator"
    )
    parser.add_argument("--version", action="version", version=VERSION)

    subparsers = parser.add_subparsers(dest="command")

    make_parser = subparsers.add_parser("make", help="Make resume from data file")
    make_parser.add_argument("position", help="Job position name")
    make_parser.add_argument(
        "-dp", "--data_path", 
        default=config.get("data_path", "data"),
        help=f"Path to data file"
    )

    lang_parser = subparsers.add_parser("lang", help="Change resume language (en/ru)")
    lang_parser.add_argument("language", nargs="?", help="Resume language (en/ru)", default=None)
    
    data_parser = subparsers.add_parser("data", help=f"Set name of data file")
    data_parser.add_argument("data_path", nargs="?", help="Name of data file", default=None)
    data_parser.add_argument("-r", "--reset", action="store_true", help="Reset to default")
    
    output_parser = subparsers.add_parser("output", help="Set path to output file")
    output_parser.add_argument("output_path", nargs="?", help="Path to output file", default=None)
    output_parser.add_argument("-r", "--reset", action="store_true", help="Reset to default")

    return parser


def main():
    with open(BASE_DIR / "config.json", encoding="utf-8") as f:
        config = json.load(f)

    parser = build_parser(config)
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "make":
        command_make(args, config)
    elif args.command == "lang":
        command_lang(args, config)
    elif args.command == "data":
        command_data(args, config)
    elif args.command == "output":
        command_output(args, config)


if __name__ == "__main__":
    main()
