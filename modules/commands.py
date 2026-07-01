import os
import re
import sys
import json
import base64
import shutil
import argparse
import subprocess

import mimetypes

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from modules.html_to_pdf import html_to_pdf
from modules.consts import BASE_DIR
from modules.defaults import CONFIG_DEFAULTS
from modules.utils import clickable_path, open_browser, write_config, remove_from_config, get_photo_from_resume
from modules.colored_text import print_error, print_success, print_warning, print_info, bullet, CType


def generate_html(data: dict, config: dict) -> Path:
    with open(BASE_DIR / "locales.json", encoding="utf-8") as f:
        locales = json.load(f)

    lang = data.get("lang", "en")
    t = locales.get(lang, locales["en"])

    photo_data_uri = None
    photo_path = BASE_DIR / "data" / data.get("photo", "photo.png")
    if Path(photo_path).exists() or Path(BASE_DIR / "data/popcat.png").exists():
        if not Path(photo_path).exists():
            print_warning(f"Warning: photo file '{photo_path}' not found. Popcat will be included in the resume instead.")
            photo_path = BASE_DIR / "data/popcat.png"
        mime, _ = mimetypes.guess_type(photo_path)
        with open(photo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        photo_data_uri = f"data:{mime};base64,{encoded}"

    template_name = config.get("template", CONFIG_DEFAULTS["template"])
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

    output_dir = config.get("output_path", CONFIG_DEFAULTS["output_path"])
    os.makedirs(output_dir, exist_ok=True)

    position = data.get("position", "resume").replace(" ", "_").lower()
    output_file = Path(output_dir) / f"resume_{position}.html"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    return output_file


def command_make(args: argparse.Namespace, config: dict):
    if args.data_file is None:
        print_error("Error: no data file specified. Specify a data file with --data_file or set a default data file using the 'data' command.")
        sys.exit(1)
    if not Path(BASE_DIR / "data" / f"{args.data_file}.json").exists():
        print_error(f"Error: file '{args.data_file}' not found")
        sys.exit(1)

    with open(BASE_DIR / "data" / f"{args.data_file}.json",
              encoding="utf-8") as f:
        data = json.load(f)

    data["position"] = args.position

    output_file = generate_html(data, config)

    write_config(config, "last_file", output_file)

    print_success(f"Done: {clickable_path(output_file)}")

    # Open browser
    open_browser(config, output_file)
    if config.get("convert_to_pdf", CONFIG_DEFAULTS["convert_to_pdf"]):
        print_info("PDF is being converted...")
        pdf_path = output_file.with_suffix(".pdf")
        if html_to_pdf(output_file, pdf_path):
            print_success(f"Done: {clickable_path(pdf_path)}")
        else:
            print_warning("Warning: no Chromium-based browser found, PDF generation skipped.")


def command_data(args: argparse.Namespace, config: dict):
    if args.data_file is None:
        data_dir = BASE_DIR / "data"

        data_files = sorted(p.stem for p in data_dir.glob("*.json"))

        current_file = config.get("data_file")
        if current_file is not None and current_file in data_files:
            data_files.remove(current_file)
            data_files.append(f"{CType.success(current_file)} (current)")

        print_info(f"Available data files:")
        print("\n".join(f" {bullet()} {file}" for file in data_files))
        if config.get('data_file') is None:
            print_warning(f"Warning: current name of resume data: {CType.error('NOT SET')}")

    elif Path.exists(BASE_DIR / "data" / f"{args.data_file}.json"):
        write_config(config, "data_file", args.data_file)
        print_success(f"Name of current data set to: {args.data_file}")
    else:
        print_error(f"Error: data '{args.data_file}' does not exist.")
        sys.exit(1)


def command_output(args: argparse.Namespace, config: dict):
    if args.output_path is None and not args.reset:
        print_info(f"Current path to output data: {\
            clickable_path(config.get("output_path", CONFIG_DEFAULTS["output_path"]))}")

    elif args.output_path is not None:
        write_config(config, "output_path", args.output_path)
        print_success(f"Output path set to: {args.output_path}")

    elif args.reset:
        try:
            remove_from_config(config, "output_path")
            print_success(f"Output path is reset to default: {\
                clickable_path(CONFIG_DEFAULTS["output_path"])}")
        except KeyError:
            print_warning(f"Output path is already default: {\
                clickable_path(CONFIG_DEFAULTS["output_path"])}")


def command_template(args: argparse.Namespace, config: dict):
    templates_dir = BASE_DIR / "templates"

    if args.template_name is None and not args.reset:

        template_files = sorted(p.stem for p in templates_dir.glob("*.html"))

        current_template = config.get("template", CONFIG_DEFAULTS["template"])
        if current_template in template_files:
            template_files.remove(current_template)
            template_files.append(f"{CType.success(current_template)} (current)")
        else:
            print_warning(f"Warning: current template: {CType.error('NOT SET')}")

        print_info(f"Available templates:")
        print("\n".join(f" {bullet()} {file}" for file in template_files))

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
            print_success(f"Template is reset to default: {CONFIG_DEFAULTS['template']}")
        except KeyError:
            print_warning(f"Template is already default: {CONFIG_DEFAULTS['template']}")


def command_last(config: dict):
    last_file = config.get("last_file")
    if last_file and Path(last_file).exists():
        print_info(f"Last generated file: {clickable_path(last_file)}")
        open_browser(config, last_file)
    else:
        print_warning("No last generated file found.")


def command_search(args: argparse.Namespace, config: dict):
    output_dir = config.get("output_path", CONFIG_DEFAULTS["output_path"])
    position = args.position.replace(" ", "_").lower()
    pattern = f"resume_*{position}*.html"

    found_files = sorted(Path(output_dir).glob(pattern), key=os.path.getmtime, reverse=True)

    if len(found_files) > 1:
        print_info(f"Found {len(found_files)} file(s) for position '{args.position}':")
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
        list_char = bullet()
        if isinstance(value, dict):
            if not value:
                return f"{indent_str}{CType.error('NOT SET')}"
            lines = []
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent_str}{CType.info(key.capitalize())}:")
                    lines.append(format_data(item, indent + 2))
                elif item is None or (isinstance(item, str) and item.strip() == ""):
                    lines.append(f"{indent_str}{CType.info(key.capitalize())}: {CType.error('NOT SET')}")
                else:
                    lines.append(f"{indent_str}{CType.info(key.capitalize())}: {item}")
            return "\n".join(lines)
        if isinstance(value, list):
            if not value:
                return f"{indent_str}{CType.error('NOT SET')}"
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(format_data(item, indent + 2))
                    lines.append("")
                elif item is None or (isinstance(item, str) and item.strip() == ""):
                    lines.append(f"{indent_str}{list_char} {CType.error('NOT SET')}")
                else:
                    lines.append(f"{indent_str}{list_char} {item}")
            return "\n".join(lines)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return f"{indent_str}{CType.error('NOT SET')}"
        return f"{indent_str}{value}"

    data_file_name = args.data_file or config.get("data_file", "data")
    data_file = BASE_DIR / f"data/{data_file_name}.json"
    if not data_file.exists():
        print_error(f"Error: data '{data_file_name}' does not exist.")
        sys.exit(1)

    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)

    print(f"{CType.header(str(f'---------- {data_file_name.upper()} ----------'))}\n{format_data(data)}")


def command_browser(args: argparse.Namespace, config: dict):
    if args.state is None:
        print_info(f"Auto-open in browser is {CType.highlight('enabled' if config.get('auto_open', CONFIG_DEFAULTS['auto_open']) else 'disabled')}")
        return
    state = args.state.lower()
    if state == "on":
        write_config(config, "auto_open", True)
        print_success("Auto-open in browser is turned ON.")
    elif state == "off":
        write_config(config, "auto_open", False)
        print_success("Auto-open in browser is turned OFF.")


def command_pdf(args: argparse.Namespace, config: dict):
    if args.state is None:
        print_info(f"Auto-conversion generated resumes to PDF is {CType.highlight("enabled" if config.get("convert_to_pdf", CONFIG_DEFAULTS["convert_to_pdf"]) else "disabled")}")
        return
    state = args.state.lower()
    if state == "on":
        write_config(config, "convert_to_pdf", True)
        print_success("Auto-conversion generated resumes to PDF is turned ON.")
    elif state == "off":
        write_config(config, "convert_to_pdf", False)
        print_success("Auto-conversion generated resumes to PDF is turned OFF.")


def command_edit(args: argparse.Namespace, config: dict):
    data_file_name = args.data or config.get("data_file", "data")
    target_file = BASE_DIR / f"data/{data_file_name}.json"
    if not target_file.exists():
        print_error(f"Error: data '{data_file_name}' does not exist.")
        sys.exit(1)
    try:
        if sys.platform == "win32":
            subprocess.run(["notepad", str(target_file)])
        else:
            subprocess.run(["nano", str(target_file)])
    except Exception as e:
        print_error(f"Error opening editor: {e}")
        sys.exit(1)


def command_rename(args: argparse.Namespace, config: dict):
    old_path = BASE_DIR / f"data/{args.old_name}.json"
    new_path = BASE_DIR / f"data/{args.new_name}.json"
    
    if new_path.exists():
        print_error(f"Error: data '{CType.highlight(args.new_name)}{CType.error("' is already exist. Choose another name.")}")
        sys.exit(1)

    if old_path.exists():
        old_path.rename(new_path)
        if config.get("data_file") == args.old_name:
            write_config(config, "data_file", args.new_name)
        print_success(f"Data '{CType.highlight(args.old_name)}{CType.success("' has been renamed to")} '{CType.highlight(args.new_name)}'")
    else:
        print_error(f"Error: data '{CType.highlight(args.old_name)}{CType.error("' does not exist.")}")
        sys.exit(1)


def command_new(args: argparse.Namespace, config: dict):
    new_file_name = args.data
    target_file = BASE_DIR / f"data/{new_file_name}.json"
    if target_file.exists():
        print_error(f"Error: data '{new_file_name}' already exists.")
        sys.exit(1)

    if args.copy:
        source_file = BASE_DIR / f"data/{args.copy}.json"
        if not source_file.exists():
            print_error(f"Error: source data '{args.copy}' does not exist.")
            sys.exit(1)
        with open(source_file, encoding="utf-8") as f:
            data = json.load(f)
    else:
        try:
            source_file = BASE_DIR / f"template.json"
            with open(source_file, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print_error("Error: template file not found. Please reinstall the application or check the README.md file and create a template.json file in the root directory.")
            sys.exit(1)

    if not Path.exists(BASE_DIR / "data/"):
        os.makedirs(BASE_DIR / "data/")

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print_success(f"New data file '{new_file_name}' has been created.")
    
    command_data(argparse.Namespace(data_file=new_file_name), config)


def command_remove(args: argparse.Namespace, config: dict):
    target_file = BASE_DIR / f"data/{args.data}.json"
    if not target_file.exists():
        print_error(f"Error: data file '{args.data}' does not exist.")
        sys.exit(1)

    approve = input(f"{CType.warning('Are you sure you want to remove \'' + args.data + '\'? (y/N): ')}")
    if approve.lower() != 'y':
        print_info("Operation cancelled.")
        return
    try:
        os.remove(target_file)
        print_success(f"Data '{args.data}' has been removed.")
        if config.get("data_file") == args.data:
            remove_from_config(config, "data_file")
    except Exception as e:
        print_error(f"Error removing data file '{args.data}': {e}")


def command_export(args: argparse.Namespace, config: dict):
    export_path = Path(args.path) / "REMAKER_EXPORT/"

    # All data
    if args.data == ["/"]:
        data_to_export = sorted((BASE_DIR / "data").iterdir())
        if not data_to_export:
            print_error("Error: no data files found.")
            sys.exit(1)
    # Specified datas
    elif args.data:
        data_to_export = []
        for name in args.data:
            f = BASE_DIR / "data" / f"{name}.json"
            if not f.exists():
                print_error(f"Error: data '{name}' does not exist.")
                sys.exit(1)
            data_to_export.append(f)
            try:
                photo_name = get_photo_from_resume(f)
                pf = BASE_DIR / "data" / photo_name
                if pf.exists():
                    data_to_export.append(pf)
                else:
                    print_warning(f"Warning: photo '{photo_name}' not found next to the data file, skipping.")
            except (KeyError, json.JSONDecodeError):
                pass
    # Current default data
    else:
        default = config.get("data_file")
        if not default:
            print_error("Error: no data file specified and default is not set.")
            sys.exit(1)
        f = BASE_DIR / "data" / f"{default}.json"
        if not f.exists():
            print_error(f"Error: data '{default}' does not exist.")
            sys.exit(1)
        data_to_export = [f]
        try:
            photo_name = get_photo_from_resume(f)
            pf = BASE_DIR / "data" / photo_name
            if pf.exists():
                data_to_export.append(pf)
            else:
                print_warning(f"Warning: photo '{photo_name}' not found next to the data file, skipping.")
        except (KeyError, json.JSONDecodeError):
            pass

    if export_path.exists() and not export_path.is_dir():
        print_error(f"Error: '{export_path}' already exists as a file, not a directory.")
        sys.exit(1)
    os.makedirs(export_path, exist_ok=True)
    for src in data_to_export:
        dst = export_path / src.name
        shutil.copy2(src, dst)

    print_success(f"Exported: {clickable_path(export_path)}")


def command_import(args: argparse.Namespace):
    source = Path(args.path)
    dest_dir = BASE_DIR / "data"
    image_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

    if not source.exists():
        print_error(f"Error: '{source}' does not exist.")
        sys.exit(1)

    def _copy(src: Path, dst: Path):
        if dst.exists():
            answer = input(f"{CType.warning(f'File \'{dst.name}\' already exists. Overwrite? (y/N): ')}")
            if answer.lower() != "y":
                print_info(f"Skipped: {src.name}")
                return
        shutil.copy2(src, dst)
        print_success(f"Imported: {clickable_path(dst)}")

    if source.is_dir():
        files = [f for f in source.iterdir()
                 if f.suffix.lower() in image_exts or f.suffix.lower() == ".json"]
        if not files:
            print_error(f"Error: no JSON or image files found in '{source}'.")
            sys.exit(1)
        for f in files:
            _copy(f, dest_dir / f.name)
    else:
        if not (source.suffix.lower() in image_exts or source.suffix.lower() == ".json"):
            print_error(f"Error: '{source.name}' is not a JSON or image file.")
            sys.exit(1)
        _copy(source, dest_dir / source.name)
        if source.suffix.lower() == ".json":
            try:
                photo_name = get_photo_from_resume(source)
                photo_src = source.parent / photo_name
                if photo_src.exists():
                    _copy(photo_src, dest_dir / photo_src.name)
                else:
                    print_warning(f"Warning: photo '{photo_name}' not found next to the data file, skipping.")
            except (KeyError, json.JSONDecodeError):
                pass


def command_convert(args: argparse.Namespace, config: dict):
    if args.name is None:
            print_error("Error: no last generated file found.")
            sys.exit(1)

    if re.match(r'^[a-zA-Z0-9_]+$', args.name):
        html_path = BASE_DIR / f"output/resume_{args.name}.html"
    else:
        html_path = Path(args.name)
    if not html_path.exists():
        print_error(f"Error: file '{html_path}' does not exist.")
        sys.exit(1)

    output_path = Path(args.output_path)

    print_info("PDF is being converted...")

    pdf_path = (output_path / Path(html_path).name).with_suffix(".pdf")

    if pdf_path.exists():
        if input(CType.warning(f"Warning: file '{pdf_path}' already exists. Rewrite? (y/N): ")).lower() != 'y':
            print_info("Operation cancelled.")
            return

    if html_to_pdf(html_path, pdf_path):
        print_success(f"Done: {clickable_path(pdf_path)}")
    else:
        print_error("Error: no Chromium-based browser found, PDF generation aborted.")


def command_config(config: dict):
    def fmt_bool(val: bool) -> str:
        return CType.success("enabled") if val else CType.error("disabled")

    last_file = config.get("last_file")
    if last_file and not Path(last_file).exists():
        last_val = CType.warning(f"{last_file} (not found)")
    elif last_file:
        last_val = clickable_path(last_file)
    else:
        last_val = CType.error("NOT SET")

    data_file = config.get("data_file")
    rows = [
        ("template", "Template",               config.get("template", CONFIG_DEFAULTS["template"])),
        ("data",     "Current data",           data_file if data_file else CType.error("NOT SET")),
        ("browser",  "Auto-open in browser",   fmt_bool(config.get("auto_open",      CONFIG_DEFAULTS["auto_open"]))),
        ("pdf",      "Auto-conversion to PDF", fmt_bool(config.get("convert_to_pdf", CONFIG_DEFAULTS["convert_to_pdf"]))),
        ("output",   "Output path",            clickable_path(config.get("output_path", CONFIG_DEFAULTS["output_path"]))),
        ("make",     "Last generated resume",  last_val),
    ]

    h = ("COMMAND", "PARAMETER", "VALUE")
    c1 = max(len(h[0]), max(len(r[0]) for r in rows))
    c2 = max(len(h[1]), max(len(r[1]) for r in rows))

    print(f" {CType.header(h[0].ljust(c1))}  {CType.header(h[1].ljust(c2))}  {CType.header(h[2])}")
    print(f" {'─' * (c1 + 2 + c2 + 2 + len(h[2]))}")
    for cmd, param, value in rows:
        print(f" {CType.highlight(cmd.ljust(c1))}  {CType.info(param.ljust(c2))}  {value}")


def command_list(args: argparse.Namespace, config: dict):
    file_type = args.type

    output_path = Path(config.get("output_path", CONFIG_DEFAULTS["output_path"]))
    if not output_path.exists():
        print_info("Output directory does not exist.")
        return

    output_path = Path(config.get("output_path", CONFIG_DEFAULTS["output_path"]))
    if not output_path.exists():
        print_info("Output directory does not exist.")
        return

    # Determine file patterns based on type
    patterns = []
    if file_type in ("html", "all"):
        patterns.append("*.html")
    if file_type in ("pdf", "all"):
        patterns.append("*.pdf")
    
    files = []
    for pattern in patterns:
        files.extend(output_path.glob(pattern))
    
    files = sorted(files)
    
    if not files:
        print_info(f"No generated resume files found ({file_type}).")
        return

    print(f"Generated resume files ({file_type}):")
    for file in files:
        size = file.stat().st_size / 1024  # Size in KB
        created = __import__("datetime").datetime.fromtimestamp(file.stat().st_ctime)
        print(f"{CType.bullet(created.strftime('%Y-%m-%d %H:%M:%S'))} - {clickable_path(file)} {CType.highlight(f'({size:.2f} KB)')}")
