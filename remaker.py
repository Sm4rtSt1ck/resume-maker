import sys
import json
import argparse

from modules.commands import *

from modules.consts import VERSION, BASE_DIR


def build_parser(config: dict) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="remaker",
        description="HTML resume generator based on Jinja2 templates.\
            Quickly make tailored resumes for different job positions \
            by swapping out data files."
    )
    parser.add_argument("--version", action="version", version=VERSION)

    subparsers = parser.add_subparsers(dest="command")

    # Make
    make_parser = subparsers.add_parser(
        "make", help="Make resume from data file")
    make_parser.add_argument("position", help="Job position name")
    make_parser.add_argument(
        "-d", "--data_file",
        default=config.get("data_file"),
        help="Path to data file"
    )

    # Data
    data_parser = subparsers.add_parser("data", help="Set name of data file")
    data_parser.add_argument("data_file", nargs="?",
                             help="Name of data file", default=None)

    # Output
    output_parser = subparsers.add_parser("output",
                                          help="Set path to output file")
    output_parser.add_argument("output_path", nargs="?",
                               help="Path to output file", default=None)
    output_parser.add_argument("-r", "--reset", action="store_true",
                               help="Reset to default")

    # Template
    template_parser = subparsers.add_parser(
        "template", help="Set or show the active HTML template")
    template_parser.add_argument(
        "template_name", nargs="?",
        help="Template name without .html extension (e.g. classic, swiss)",
        default=None
    )
    template_parser.add_argument("-r", "--reset", action="store_true",
                                 help="Reset to default (classic)")
    
    # Last
    last_parser = subparsers.add_parser(
        "last", help="Show the last generated resume file")
    
    # Search
    search_parser = subparsers.add_parser(
        "search", help="Get created resume files for a position")
    search_parser.add_argument("position", help="Job position name")
    
    # Show
    show_parser = subparsers.add_parser(
        "show", help="Show data in data file")
    show_parser.add_argument("data_file", nargs="?", default=None,
                             help="Name of data file to show")
    
    # Browser
    browser_parser = subparsers.add_parser(
        "browser", help="Automatically open resumes in browser after generation or finding")
    browser_parser.add_argument("state", nargs="?", choices=["on", "off"], help="Turn auto-open in browser on or off")

    # Convert to pdf
    pdf_parser = subparsers.add_parser(
        "pdf", help="Automatically convert generated resumes to PDF"
    )
    pdf_parser.add_argument("state", nargs="?", choices=["on", "off"], help="Turn auto-convert generated resumes to PDF on or off")

    rename_parser = subparsers.add_parser(
        "rename", help="Rename data"
    )
    rename_parser.add_argument("old_name")
    rename_parser.add_argument("new_name")

    # Edit
    edit_parser = subparsers.add_parser(
        "edit", help="Edit data file of a resume")
    edit_parser.add_argument("data", nargs="?", default=None,
                             help="Name of data file to edit")

    # New
    new_parser = subparsers.add_parser(
        "new", help="Create a new data file for a resume")
    new_parser.add_argument("data", help="Name of new data file")
    new_parser.add_argument("-c", "--copy", help="Copy from other data file")
    
    # Remove
    remove_parser = subparsers.add_parser(
        "remove", help="Remove a data file")
    remove_parser.add_argument("data", help="Name of data file to remove")
    
    # Export
    export_parser = subparsers.add_parser(
        "export", help="Export data")
    export_parser.add_argument("path", help="Path to exported data")
    export_parser.add_argument("data", nargs="*", help="Name(s) of data to export (empty - current default, / - all)")

    # Import
    import_parser = subparsers.add_parser(
        "import", help="Import data")
    import_parser.add_argument("path", help="Path to imported data/folder")

    convert_parser = subparsers.add_parser(
        "convert", help="Convert HTML resume to PDF"
    )
    convert_parser.add_argument("-n", "--name", default=config.get("last_file", None), nargs="?", help="Resume vacancy name / path to resume (e.g. 'backend_developer' or '~/Downloads/resume_backend_developer.html')")
    convert_parser.add_argument("-o", "--output_path", default=config.get("output_path", BASE_DIR / "output/"), nargs="?", help="Output path (empty - current output path)")

    return parser


def _load_config() -> dict:
    config_path = BASE_DIR / "config.json"
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    config = _load_config()

    parser = build_parser(config)
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "make":
        command_make(args, config)
    elif args.command == "data":
        command_data(args, config)
    elif args.command == "output":
        command_output(args, config)
    elif args.command == "template":
        command_template(args, config)
    elif args.command == "last":
        command_last(config)
    elif args.command == "search":
        command_search(args, config)
    elif args.command == "show":
        command_show(args, config)
    elif args.command == "browser":
        command_browser(args, config)
    elif args.command == "pdf":
        command_pdf(args, config)
    elif args.command == "edit":
        command_edit(args, config)
    elif args.command == "new":
        command_new(args, config)
    elif args.command == "remove":
        command_remove(args, config)
    elif args.command == "export":
        command_export(args, config)
    elif args.command == "import":
        command_import(args)
    elif args.command == "rename":
        command_rename(args, config)
    elif args.command == "convert":
        command_convert(args, config)


if __name__ == "__main__":
    main()
