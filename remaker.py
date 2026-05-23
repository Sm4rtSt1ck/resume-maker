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

    make_parser = subparsers.add_parser(
        "make", help="Make resume from data file")
    make_parser.add_argument("position", help="Job position name")
    make_parser.add_argument(
        "-d", "--data_file",
        default=config.get("data_file", "data"),
        help=f"Path to data file"
    )

    # Data
    data_parser = subparsers.add_parser("data", help=f"Set name of data file")
    data_parser.add_argument("data_file", nargs="?",
                             help="Name of data file", default=None)
    data_parser.add_argument("-r", "--reset", action="store_true",
                             help="Reset to default")

    # Output
    output_parser = subparsers.add_parser("output",
                                          help="Set path to output file")
    output_parser.add_argument("output_path", nargs="?",
                               help="Path to output file", default=None)
    output_parser.add_argument("-r", "--reset", action="store_true",
                               help="Reset to default")

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
    elif args.command == "data":
        command_data(args, config)
    elif args.command == "output":
        command_output(args, config)


if __name__ == "__main__":
    main()
